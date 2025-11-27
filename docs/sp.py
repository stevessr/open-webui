"""
title: Gemini with search & code & OpenWebUI Tools (Pseudo-streaming)
licence: MIT
author: stevessr
author_url: https://linux.do/t/topic/759930
funding_url: https://linux.do/t/topic/759930
version: 0.3
"""

import json
import logging
import time
import uuid
import re
from typing import (
    AsyncIterable,
    Optional,
    Callable,
    Awaitable,
    AsyncGenerator,
    List,
    Dict,
    Any,
)
import asyncio

import httpx
from pydantic import BaseModel, Field

# 假设 open_webui.env 存在，如果不存在，则使用标准的 logging 配置
try:
    from open_webui.env import SRC_LOG_LEVELS

    log_level = SRC_LOG_LEVELS["MAIN"]
except ImportError:
    log_level = logging.INFO

# 配置日志记录器
logging.basicConfig(
    level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)


class Pipe:
    """
    一个用于与 Gemini API 交互的 Manifold 风格管道。
    """

    class Valves(BaseModel):
        # Pydantic 模型，用于配置管道的阀门（即设置）
        base_url: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Gemini API 的基础 URL",
        )
        api_key: str = Field(default="", description="Gemini API 密钥")
        timeout: int = Field(default=600, description="整个请求的超时时间（秒）")

        # 新增：流空闲超时，用于检测中断的流
        stream_idle_timeout: int = Field(
            default=30, description="流空闲超时时间（秒）。"
        )

        # 模型配置
        model_id: str = Field(
            default="gemini-2.5-flash-lite",
            description="UI 中使用的模型 ID。",
        )
        model_display_name: str = Field(
            default="Gemini 2.5 Flash Lite 研究", description="UI 中显示的模型名称。"
        )
        api_model: str = Field(
            default="gemini-2.5-flash-lite",
            description="用于 API 调用的实际 Gemini 模型名称。",
        )

    class UserValves(BaseModel):
        # 思考预算配置
        thinking_budget: int = Field(
            default=-1,
            description="Gemini API 的思考预算（thinkingBudget）。设置为 0 关闭思考，-1 开启动态思考。",
        )
        include_thoughts: bool = Field(
            default=True, description="是否返回 Gemini 的思考摘要"
        )
        # 输出延迟配置
        output_delay: float = Field(
            default=0.01,
            description="输出延迟时间（秒）。在字符模式下为每个字符间的延迟，在块模式下为每个块间的延迟。设置为 0 以禁用。",
        )
        # 块状输出配置
        block_size: int = Field(
            default=10,
            description="每个输出块的字符数。当大于 1 时分块输出，为 1 时逐字符输出，小于 0 时按空格分块输出。",
        )
        # temperature 和 top_P 配置
        temperature: float = Field(default=0.7, description="控制生成文本的随机性。")
        top_p: float = Field(default=0.9, description="控制生成文本的多样性。")

    def __init__(self):
        self.type = "manifold"
        self.name = ""
        self.valves = self.Valves()
        self.emitter: Optional[Callable[[dict], Awaitable[None]]] = None
        self.default: Optional[dict] = {
            "thinking_budget": -1,
            "include_thoughts": True,
            "output_delay": 0.01,
            "block_size": 10,
            "temperature": 0.7,
            "top_p": 0.9,
        }
        logger.info(f"管道 '{self.name}' 已初始化。")

    async def emit_status(self, message: str, done: bool = False):
        if self.emitter:
            await self.emitter(
                {
                    "type": "status",
                    "data": {"description": str(message)[:500], "done": done},
                }
            )

    def get_models(self) -> List[dict]:
        return [
            {"id": self.valves.model_id, "name": self.valves.model_display_name},
        ]

    def pipes(self) -> List[dict]:
        return self.get_models()

    def split_html_tags(self, text: str) -> List[str]:
        """
        将文本分割为 HTML 标签和普通文本块的列表
        例如："Hello <b>world</b>!" -> ["Hello ", "<b>", "world", "</b>", "!"]
        """
        pattern = r"(<[^>]+>)"
        return re.split(pattern, text)

    def convert_openai_tools_to_gemini(self, tools: List[Dict]) -> List[Dict]:
        """
        修复版：将 OpenAI 工具转换为 Gemini 格式。
        """
        gemini_funcs = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                name = func.get("name")
                description = func.get("description", "")
                parameters = func.get("parameters", {})

                # Gemini 不支持 additionalProperties: false 在某些层级，
                # 但通常 OpenAI 格式可以直接传递，主要区别在于 properties 的结构。
                # 确保 parameters 是一个对象
                if (
                    parameters.get("type") != "object"
                    and "properties" not in parameters
                ):
                    parameters = {"type": "object", "properties": {}}

                gemini_func = {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                }
                gemini_funcs.append(gemini_func)
        return gemini_funcs

    def insert_grounding_citations(self, text: str, metadata: Dict) -> str:
        """
        根据 groundingMetadata 将引用内嵌到文本中。
        """
        if not metadata or "groundingChunks" not in metadata or "groundingSupports" not in metadata:
            return text

        chunks = metadata["groundingChunks"]
        supports = metadata["groundingSupports"]

        # 收集所有的插入点
        # 格式：(index, citation_text)
        insertions = []

        for support in supports:
            segment = support.get("segment", {})
            end_index = segment.get("endIndex")
            chunk_indices = support.get("groundingChunkIndices", [])

            if end_index is not None and chunk_indices:
                # 构建引用字符串，例如 [1](url), [2](url)
                citations = []
                for idx in chunk_indices:
                    if 0 <= idx < len(chunks):
                        chunk = chunks[idx]
                        if "web" in chunk:
                            uri = chunk["web"].get("uri", "")
                            # title = chunk["web"].get("title", f"Source {idx+1}")
                            # 使用 Markdown 链接格式 [n](uri)
                            if uri:
                                citations.append(f"[{idx + 1}]({uri})")
                
                if citations:
                    citation_str = " " + ", ".join(citations)
                    insertions.append((end_index, citation_str))

        # 按位置降序排序，以便从后往前插入，不影响前面的索引
        insertions.sort(key=lambda x: x[0], reverse=True)

        # 执行插入
        result_text = text
        for idx, citation_str in insertions:
            # 确保索引在范围内 (API 应该保证，但为了安全)
            if 0 <= idx <= len(result_text):
                result_text = result_text[:idx] + citation_str + result_text[idx:]
        
        return result_text

    async def process_stream(
        self,
        response: httpx.Response,
        detected_tool_calls: List[Dict],
        accumulated_text: List[str],
    ) -> AsyncGenerator[str, None]:
        """
        处理来自 Gemini API 的 SSE 流。
        注意：为了支持内嵌引用 (Inline Grounding)，普通文本会被缓冲直到流结束或收到元数据，
        而思考过程 (Thought) 会实时流式传输。
        """
        finish_reason_received = False
        stream_iterator = response.aiter_lines()
        content_yielded = False
        is_thinking = False
        
        # 缓冲区
        text_buffer = []
        grounding_metadata = None

        try:
            while True:
                try:
                    line = await asyncio.wait_for(
                        stream_iterator.__anext__(),
                        timeout=self.valves.stream_idle_timeout,
                    )
                    if not line.strip() or not line.startswith("data: "):
                        continue
                    line = line[6:]

                    try:
                        chunk = json.loads(line)
                        if "error" in chunk:
                            error_msg = f"🚨 API Error: {chunk['error'].get('message')}"
                            logger.error(error_msg)
                            yield error_msg
                            return

                        candidates = chunk.get("candidates", [])
                        if candidates:
                            candidate = candidates[0]

                            # 1. 捕获 Grounding Metadata (通常在最后一个 chunk)
                            if "groundingMetadata" in candidate:
                                grounding_metadata = candidate["groundingMetadata"]

                            if (
                                "content" in candidate
                                and "parts" in candidate["content"]
                            ):
                                for part in candidate["content"]["parts"]:
                                    # 2. 检测工具调用
                                    if "functionCall" in part:
                                        logger.info(
                                            f"检测到函数调用：{part['functionCall']}"
                                        )
                                        detected_tool_calls.append(part["functionCall"])
                                        continue  # 工具调用不显示文本

                                    # 3. 处理文本和思考
                                    text_content = part.get("text", "")
                                    is_thought = part.get("thought", False)

                                    if text_content:
                                        content_yielded = True

                                        if is_thought:
                                            # 如果是思考，直接流式输出
                                            if not is_thinking:
                                                yield "<think>"
                                                is_thinking = True
                                            yield text_content
                                        else:
                                            # 如果是正文，先结束思考标签（如果有关闭的话）
                                            if is_thinking:
                                                yield "</think>"
                                                is_thinking = False
                                            
                                            # 累积正文到 history 用于下一次 context
                                            accumulated_text.append(text_content)
                                            # 缓冲正文用于最后处理引用
                                            text_buffer.append(text_content)

                        if candidates and candidates[0].get("finishReason"):
                            finish_reason_received = True

                    except json.JSONDecodeError:
                        pass
                    except (KeyError, IndexError):
                        pass

                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    yield "🚨 Stream Timeout"
                    return

            if is_thinking:
                yield "</think>"

        finally:
            # 流结束，处理缓冲的文本和引用
            full_text = "".join(text_buffer)
            
            if grounding_metadata and full_text:
                # 如果有引用元数据，进行内嵌处理
                cited_text = self.insert_grounding_citations(full_text, grounding_metadata)
                yield cited_text
            elif full_text:
                # 如果没有元数据，直接输出缓冲的文本
                yield full_text

            if (
                not finish_reason_received
                and not detected_tool_calls
                and content_yielded
            ):
                logger.warning("Stream ended unexpectedly.")

    async def get_request_stream(
        self,
        messages: list,
        model_name: str,
        tools: Optional[List[dict]] = None,
        __user__: Optional[dict] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        user_valves = (__user__ or self.default).get("valves", self.UserValves())
        api_model = self.valves.api_model

        # 1. 转换消息历史
        current_messages = []
        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content")
            parts = []

            if isinstance(content, str):
                parts.append({"text": content})
            elif isinstance(content, list):
                for part in content:
                    if part.get("type") == "text":
                        parts.append({"text": part.get("text", "")})
                    elif part.get("type") == "image_url":
                        # 简化的图片处理
                        url = part.get("image_url", {}).get("url", "")
                        if "base64," in url:
                            header, data = url.split(",", 1)
                            mime = header.split(":")[1].split(";")[0]
                            parts.append(
                                {"inlineData": {"mimeType": mime, "data": data}}
                            )

            # 处理 OpenWebUI 历史中的 tool_calls (如果是多轮对话)
            # 这部分通常比较复杂，因为 OpenWebUI 传回的历史格式可能已经是 OpenAI 格式
            # 我们需要确保它能被正确映射回 Gemini 格式。
            # 暂时假设 OpenWebUI 传入的 message history 主要是 text，工具历史由本函数内部循环维护。

            if parts:
                current_messages.append({"role": role, "parts": parts})

        if current_messages and current_messages[-1]["role"] == "model":
            current_messages.append({"role": "user", "parts": [{"text": "Continue"}]})

        # 2. 工具配置
        gemini_tools = [{"googleSearch": {}}]
        if tools:
            converted = self.convert_openai_tools_to_gemini(tools)
            if converted:
                gemini_tools.append({"function_declarations": converted})

        # 3. 执行循环 (处理工具调用)
        MAX_LOOPS = 5
        loop_count = 0

        while loop_count < MAX_LOOPS:
            loop_count += 1

            payload = {
                "contents": current_messages,
                "tools": gemini_tools,
                "generationConfig": {
                    "temperature": user_valves.temperature,
                    "topP": user_valves.top_p,
                    "thinkingConfig": {
                        "includeThoughts": user_valves.include_thoughts,
                        "thinkingBudget": user_valves.thinking_budget,
                    }
                    if "thinking" in api_model or "flash" in api_model
                    else None,  # 简单判定
                },
            }
            # 清理 None 值
            if not payload["generationConfig"]["thinkingConfig"]:
                del payload["generationConfig"]["thinkingConfig"]

            url = f"/v1beta/models/{api_model}:streamGenerateContent?key={self.valves.api_key}&alt=sse"
            detected_tool_calls = []
            accumulated_text_parts = []  # 本轮生成的文本

            async with httpx.AsyncClient(
                base_url=self.valves.base_url, timeout=self.valves.timeout
            ) as client:
                if loop_count > 1:
                    await self.emit_status("Processing tool outputs...", done=False)

                try:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code != 200:
                            err = await response.aread()
                            yield f"🚨 Error {response.status_code}: {err.decode()}"
                            return

                        async for chunk in self.process_stream(
                            response, detected_tool_calls, accumulated_text_parts
                        ):
                            yield chunk
                except Exception as e:
                    yield f"🚨 Network Error: {e}"
                    return

            # 4. 如果没有工具调用，结束
            if not detected_tool_calls:
                break

            # 5. 处理工具调用
            if not __event_call__:
                logger.warning("Tool call detected but no handler available.")
                break

            # === 关键修正：构建正确的历史记录 ===

            # A. 添加模型回合 (Model Turn)
            # 必须包含本轮生成的所有文本 + 工具调用
            model_parts = []
            full_text = "".join(accumulated_text_parts)
            if full_text:
                model_parts.append({"text": full_text})

            for tc in detected_tool_calls:
                model_parts.append({"functionCall": tc})

            current_messages.append({"role": "model", "parts": model_parts})

            # B. 执行工具并添加函数回合 (Function Turn)
            function_parts = []
            for tc in detected_tool_calls:
                func_name = tc.get("name")
                func_args = tc.get("args", {})

                await self.emit_status(f"🛠️ Calling: {func_name}...", done=False)

                try:
                    # OpenWebUI 期望 arguments 是 dict
                    result = await __event_call__(
                        {"name": func_name, "arguments": func_args}
                    )
                    
                    # 将工具返回值作为内容的一部分返回
                    if result:
                        yield str(result)

                    # Gemini 期望 response 是一个 Object，不能是纯字符串
                    # 如果结果是字符串，包装它
                    content_to_send = result
                    if not isinstance(result, (dict, list)):
                        content_to_send = {"result": str(result)}

                    function_parts.append(
                        {
                            "functionResponse": {
                                "name": func_name,
                                "response": content_to_send,
                            }
                        }
                    )
                except Exception as e:
                    logger.error(f"工具 {func_name} 执行失败：{e}")
                    function_parts.append(
                        {
                            "functionResponse": {
                                "name": func_name,
                                "response": {"error": str(e)},
                            }
                        }
                    )

            # 添加 Function 响应消息
            # v1beta REST API 中，Function Response 的 role 通常是 'function'
            current_messages.append({"role": "function", "parts": function_parts})

            # 循环继续，发送包含结果的新请求

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __tools__: Optional[List[dict]] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        管道入口。
        """
        self.emitter = __event_emitter__
        user_valves = (__user__ or self.default).get("valves", self.UserValves())
        request_id = str(uuid.uuid4())

        # 提取 Open WebUI 传递的工具定义
        # Open WebUI 通常在 body 中传递 'tools' (OpenAI 格式)
        incoming_tools = body.get("tools", [])

        try:
            await self.emit_status("正在验证请求负载...", done=False)
            if not isinstance(body, dict):
                error_msg = "❌ 错误：请求体必须是有效的 JSON 对象。"
                yield error_msg
                await self.emit_status("错误：无效的请求体。", done=True)
                return
            messages = body.get("messages")
            if not messages or not isinstance(messages, list):
                error_msg = "❌ 错误：请求体必须包含一个有效的 'messages' 列表。"
                yield error_msg
                await self.emit_status(
                    "错误：缺少或无效的 'messages' 列表。", done=True
                )
                return

            if not self.valves.api_key:
                yield "❌ Error: API Key not set."
                return

            model_id = body.get("model", self.valves.model_id)

            await self.emit_status(f"正在使用模型 '{model_id}' 开始生成...", done=False)

            stream_had_error = False
            full_response = ""
            async for chunk in self.get_request_stream(
                messages=messages,
                model_name=model_id,
                tools=incoming_tools,
                __user__=__user__,
                __event_call__=__event_call__,
            ):
                if chunk.startswith("🚨"):
                    stream_had_error = True
                    yield chunk
                    continue

                full_response += chunk

                # 输出处理逻辑 (块/字符/延迟)
                if user_valves.block_size > 1:
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            yield chunk_part
                        else:
                            for i in range(0, len(chunk_part), user_valves.block_size):
                                block = chunk_part[i : i + user_valves.block_size]
                                if block:
                                    yield block
                                    if user_valves.output_delay > 0:
                                        await asyncio.sleep(user_valves.output_delay)
                elif user_valves.block_size < 0:
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            yield chunk_part
                        else:
                            parts = re.split(r"(\s+)", chunk_part)
                            for part in parts:
                                if part:
                                    yield part
                                    if user_valves.output_delay > 0:
                                        await asyncio.sleep(user_valves.output_delay)
                else:
                    skip = False
                    for char in chunk:
                        yield char
                        if char == "<":
                            skip = True
                        elif char == ">":
                            skip = False
                        if skip:
                            continue
                        if user_valves.output_delay > 0:
                            await asyncio.sleep(user_valves.output_delay)

            if not full_response and not stream_had_error:
                logger.warning(f"[{request_id}] 响应流结束但未收到任何文本内容。")
                yield ""

            if not stream_had_error:
                logger.info(f"[{request_id}] 内容生成成功且无错误。")
                await self.emit_status("生成完成。", done=True)
            else:
                logger.warning(f"[{request_id}] 内容生成期间发生错误。")

        except Exception as e:
            error_msg = f"❌ 管道中发生意外的系统错误：{e}"
            logger.exception(f"[{request_id}] {error_msg}")
            await self.emit_status(f"致命错误：{e}", done=True)
            yield error_msg

        logger.info(f"[{request_id}] 管道处理结束。")