"""
title: Gemini with search & code (Pseudo-streaming) - Robust Version with Detailed Token Calculation
licence: MIT
"""

import json
import logging
import time
import uuid
import re
from typing import AsyncIterable, Optional, Callable, Awaitable, AsyncGenerator, List
import asyncio  # 引入 asyncio 用于超时和延迟

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
    该管道处理流式响应并提供状态更新。
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
            default=30, description="在假定连接中断之前，等待新数据的最长时间（秒）。"
        )

        # 模型配置
        model_id: str = Field(
            default="gemini-2.5-flash",
            description="UI 中使用的模型 ID。",
        )
        model_display_name: str = Field(
            default="Gemini 2.5 Flash 研究", description="UI 中显示的模型名称。"
        )
        api_model: str = Field(
            default="gemini-2.5-flash",
            description="用于 API 调用的实际 Gemini 模型名称。",
        )
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
        logger.info(f"管道 '{self.name}' 已初始化。")

    async def emit_status(self, message: str, done: bool = False):
        if self.emitter:
            if message.strip().startswith("<thinking>") and message.strip().endswith(
                "</thinking>"
            ):
                status_payload = {
                    "type": "status",
                    "data": {"description": message, "done": done},
                }
            else:
                status_payload = {
                    "type": "status",
                    "data": {"description": str(message)[:500], "done": done},
                }
            logger.debug(f"发送状态更新：{status_payload}")
            await self.emitter(status_payload)

    def get_models(self) -> List[dict]:
        return [
            {
                "id": self.valves.model_id,
                "name": self.valves.model_display_name,
            },
        ]

    def pipes(self) -> List[dict]:
        return self.get_models()

    def split_html_tags(self, text: str) -> List[str]:
        """
        将文本分割为 HTML 标签和普通文本块的列表
        例如："Hello <b>world</b>!" -> ["Hello ", "<b>", "world", "</b>", "!"]
        """
        import re

        pattern = r"(<[^>]+>)"
        return re.split(pattern, text)

    async def process_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[str, None]:
        """
        处理来自 Gemini API 的服务器发送事件 (SSE) 流，并增加了超时和完整性检查。
        （已修正，可处理“思考”内容为布尔值或字符串的情况）
        """
        logger.info("开始处理 API 响应流。")
        finish_reason_received = False
        stream_iterator = response.aiter_lines()
        content_yielded = False

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
                        logger.debug(f"收到并解析了数据块：{chunk}")

                        if "error" in chunk:
                            error_detail = chunk.get("error", {}).get(
                                "message", "流中发生未知错误"
                            )
                            error_msg = f"🚨 Gemini API 错误：{error_detail}"
                            logger.error(error_msg)
                            await self.emit_status(error_msg, done=True)
                            yield error_msg
                            return

                        if "candidates" in chunk:
                            for candidate in chunk.get("candidates", []):
                                if (
                                    "content" in candidate
                                    and "parts" in candidate["content"]
                                ):
                                    for part in candidate["content"]["parts"]:
                                        is_thought_part = part.get("thought") is True
                                        text_content = part.get("text", "")

                                        if not text_content.strip():
                                            continue

                                        if is_thought_part:
                                            thought_text = text_content.strip()
                                            quoted_lines = [
                                                f"> {line}"
                                                for line in thought_text.splitlines()
                                            ]
                                            quoted_thought = "\n".join(quoted_lines)
                                            thought_msg = (
                                                f"<think>{quoted_thought}</think>"
                                            )
                                            yield thought_msg
                                            content_yielded = True
                                        else:
                                            yield text_content
                                            content_yielded = True

                        # --- 核心修改开始：分离思考/工具和其他部分的 Token 计算 ---
                        if usage_metadata := chunk.get("usageMetadata"):
                            usage_parts = []
                            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                            candidates_tokens = usage_metadata.get(
                                "candidatesTokenCount", 0
                            )
                            total_tokens = usage_metadata.get("totalTokenCount", 0)

                            # 根据文档，这些是可能出现的与“思考”相关的 Token 字段。
                            thoughts_tokens = usage_metadata.get(
                                "thoughtsTokenCount", 0
                            )
                            tool_use_tokens = usage_metadata.get("toolUseTokenCount", 0)
                            grounding_tokens = usage_metadata.get(
                                "groundingTokenCount", 0
                            )

                            # 将所有非内容生成的 Token 加总
                            thinking_and_tool_tokens = (
                                thoughts_tokens + tool_use_tokens + grounding_tokens
                            )

                            # 从候选 Token 总数中减去思考/工具 Token，得到纯文本输出 Token
                            output_text_tokens = (
                                candidates_tokens - thinking_and_tool_tokens
                            )

                            usage_parts.append(f"输入：{prompt_tokens} tokens")

                            # 仅当纯文本输出 Token 大于 0 时显示
                            if output_text_tokens > 0:
                                usage_parts.append(
                                    f"输出 (内容): {output_text_tokens} tokens"
                                )

                            # 仅当思考/工具 Token 大于 0 时显示
                            if thinking_and_tool_tokens > 0:
                                usage_parts.append(
                                    f"输出 (思考/工具): {thinking_and_tool_tokens} tokens"
                                )

                            usage_parts.append(f"总计：{total_tokens} tokens")

                            usage_msg = (
                                f"用量信息：{', '.join(usage_parts)}"
                                if usage_parts
                                else "用量信息可用"
                            )
                            logger.info(usage_msg)
                            await self.emit_status(usage_msg, done=False)
                        # --- 核心修改结束 ---

                        if finish_reason := chunk.get("candidates", [{}])[0].get(
                            "finishReason"
                        ):
                            logger.info(f"从 API 收到完成原因：{finish_reason}")
                            finish_reason_received = True

                    except json.JSONDecodeError:
                        logger.warning(f"解码 JSON 行失败：{line}. 跳过此行。")
                        await self.emit_status(
                            f"警告：无法解析一个数据块。可能存在格式问题。", done=False
                        )
                    except (KeyError, IndexError) as e:
                        logger.debug(
                            f"无法从数据块中提取文本或元数据：{line}. 错误：{e}. 跳过此块。"
                        )
                        await self.emit_status(
                            f"警告：接收到未知格式的数据块。", done=False
                        )

                except StopAsyncIteration:
                    logger.info("响应流正常结束。")
                    break
                except asyncio.TimeoutError:
                    error_msg = f"🚨 流超时：在 {self.valves.stream_idle_timeout} 秒内未收到新数据，连接可能已中断。"
                    logger.error(error_msg)
                    await self.emit_status(error_msg, done=True)
                    yield error_msg
                    return

        finally:
            if not finish_reason_received:
                warning_msg = "警告：API 响应流已结束，但未收到明确的完成信号（finishReason）。这可能表示流被意外中断或未完全发送。"
                logger.warning(warning_msg)
                await self.emit_status(warning_msg, done=True)
            elif not content_yielded and finish_reason_received:
                logger.debug(
                    "Stream ended with finish reason but no text content was yielded."
                )

        logger.info("响应流处理完毕。")

    async def get_request_stream(
        self, messages: list, model_name: str
    ) -> AsyncGenerator[str, None]:
        """构建请求并从 Gemini API 流式传输响应。"""
        api_model = self.valves.api_model
        logger.info(
            f"为 UI 模型 '{model_name}' 准备请求，使用 API 模型 '{api_model}'。"
        )

        gemini_contents = []

        for msg in messages:
            role = "user" if msg.get("role") == "user" else "model"
            content = msg.get("content")
            parts = []
            if isinstance(content, str):
                parts.append({"text": content})
            elif isinstance(content, list):
                for part in content:
                    part_type = part.get("type")
                    if part_type == "text":
                        parts.append({"text": part.get("text", "")})
                    elif part_type == "image_url":
                        image_url = part.get("image_url", {}).get("url", "")
                        if (
                            image_url.startswith("data:image")
                            and ";base64," in image_url
                        ):
                            try:
                                header, encoded_data = image_url.split(",", 1)
                                mime_type = header.split(":", 1)[1].split(";", 1)[0]
                                parts.append(
                                    {
                                        "inlineData": {
                                            "mimeType": mime_type,
                                            "data": encoded_data,
                                        }
                                    }
                                )
                            except (ValueError, IndexError) as e:
                                logger.error(
                                    f"Error parsing image data URI: {e}. Skipping image part."
                                )

                        else:
                            logger.warning(
                                f"Unsupported image URL format. Only 'data:image' URIs are supported."
                            )
            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        if gemini_contents and gemini_contents[-1]["role"] == "model":
            gemini_contents.append({"role": "user", "parts": [{"text": "Continue"}]})
            logger.warning(
                "Added a dummy 'user' turn to continue the conversation after a 'model' turn."
            )

        gemini_tools = [
            {"googleSearch": {}},
            {"code_execution": {}},
            {"url_context": {}},
        ]

        data = {
            "contents": gemini_contents,
            "tools": gemini_tools,
            "generationConfig": {
                "temperature": self.valves.temperature,
                "topP": self.valves.top_p,
                "thinkingConfig": {
                    "includeThoughts": self.valves.include_thoughts,
                    "thinkingBudget": self.valves.thinking_budget,
                },
            },
        }

        url = f"/v1beta/models/{api_model}:streamGenerateContent?key={self.valves.api_key}&alt=sse"

        try:
            async with httpx.AsyncClient(
                base_url=self.valves.base_url,
                trust_env=True,
                timeout=self.valves.timeout,
            ) as client:
                await self.emit_status(
                    f"正在向 Gemini 模型发送请求：{api_model}", done=False
                )
                async with client.stream("POST", url, json=data) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_message = f"🚨 Gemini API 错误：{response.status_code} - {error_content.decode()}"
                        await self.emit_status(error_message, done=True)
                        yield error_message
                        return

                    async for content in self.process_stream(response):
                        yield content

        except httpx.ConnectError as e:
            error_msg = f"🚨 连接错误：无法连接到 {self.valves.base_url}。请检查网络连接或基础 URL。 {e}"
            logger.exception(error_msg)
            await self.emit_status(error_msg, done=True)
            yield error_msg
        except httpx.TimeoutException:
            error_msg = (
                f"🚨 请求超时：对 Gemini API 的请求在 {self.valves.timeout} 秒后超时。"
                f"请检查网络或增加管道超时设置。"
            )
            logger.error(error_msg)
            await self.emit_status(error_msg, done=True)
            yield error_msg
        except Exception as e:
            error_msg = f"🚨 发生意外错误：{e}"
            logger.exception(f"在 get_request_stream 中发生意外错误：{e}")
            await self.emit_status(error_msg, done=True)
            yield error_msg

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        管道的主入口点。
        它验证请求，调用 Gemini API，并以伪流式（逐字）的方式返回响应。
        """
        self.emitter = __event_emitter__
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] 管道开始处理新请求。")
        logger.debug(f"[{request_id}] 收到的请求体：{body}")

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
                error_msg = (
                    "❌ 错误：Gemini API 密钥未设置。请在管道配置中提供 API 密钥。"
                )
                yield error_msg
                await self.emit_status(error_msg, done=True)
                return

            logger.info(f"[{request_id}] 请求负载验证通过。")

            model_id = body.get("model", self.valves.model_id)

            await self.emit_status(f"正在使用模型 '{model_id}' 开始生成...", done=False)

            stream_had_error = False
            full_response = ""

            async for chunk in self.get_request_stream(messages, model_id):
                if chunk.startswith("🚨"):
                    stream_had_error = True
                    yield chunk
                    continue

                full_response += chunk

                # 根据配置选择输出方式：块状输出、字符输出或空格分块输出
                if self.valves.block_size > 1:
                    # 块状输出模式 - 先分离 HTML 标签
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            # HTML 标签直接输出，不分块
                            yield chunk_part
                        else:
                            # 普通文本分块输出
                            for i in range(0, len(chunk_part), self.valves.block_size):
                                block = chunk_part[i : i + self.valves.block_size]
                                if block:  # 避免输出空块
                                    yield block
                                    if self.valves.output_delay > 0:
                                        await asyncio.sleep(self.valves.output_delay)
                elif self.valves.block_size < 0:
                    # 按空格分块输出模式 - 先分离 HTML 标签
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            # HTML 标签直接输出，不分块
                            yield chunk_part
                        else:
                            # 普通文本按空格分块输出
                            # 修复：使用 re.split(r'(\s+)') 而不是 split()
                            # split() 会丢弃所有空白符（包括换行符），导致代码块和段落合并。
                            # re.split(r'(\s+)') 会保留分隔符（即空格、换行符等），防止格式丢失。
                            parts = re.split(r"(\s+)", chunk_part)
                            for part in parts:
                                if part:  # 避免输出空串
                                    yield part
                                    if self.valves.output_delay > 0:
                                        await asyncio.sleep(self.valves.output_delay)
                else:
                    # 原有的字符输出模式
                    skip = False
                    for char in chunk:
                        yield char

                        if char == "<":
                            skip = True
                        elif char == ">":
                            skip = False

                        if skip:
                            continue
                        if self.valves.output_delay > 0:
                            await asyncio.sleep(self.valves.output_delay)

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
