"""
title: Gemini with search & code (Pseudo-streaming) - Robust Version with Independent Judgment
licence: MIT
"""

import json
import logging
import time
import uuid
from typing import Optional, Callable, Awaitable, AsyncGenerator, List
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
    该管道处理流式响应，并在每轮结束后使用模型独立判断是否需要继续生成。
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
            default="gemini-2.5-flash-lite",
            description="UI 中使用的模型 ID。",
        )
        model_display_name: str = Field(
            default="Gemini 2.5 Flash lite 研究", description="UI 中显示的模型名称。"
        )
        api_model: str = Field(
            default="gemini-2.5-flash-lite",
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
        self.name = "Gemini 2.5 Flash lite 研究"
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
        pattern = r'(<[^>]+>)'
        return re.split(pattern, text)

    async def process_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[str, None]:
        """
        处理来自 Gemini API 的服务器发送事件 (SSE) 流，并增加了超时和完整性检查。
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
                        # logger.debug(f"收到并解析了数据块：{chunk}")

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

                        # --- Token 计算逻辑 ---
                        if usage_metadata := chunk.get("usageMetadata"):
                            usage_parts = []
                            prompt_tokens = usage_metadata.get("promptTokenCount", 0)
                            candidates_tokens = usage_metadata.get(
                                "candidatesTokenCount", 0
                            )
                            total_tokens = usage_metadata.get("totalTokenCount", 0)

                            thoughts_tokens = usage_metadata.get(
                                "thoughtsTokenCount", 0
                            )
                            tool_use_tokens = usage_metadata.get("toolUseTokenCount", 0)
                            grounding_tokens = usage_metadata.get(
                                "groundingTokenCount", 0
                            )

                            thinking_and_tool_tokens = (
                                thoughts_tokens + tool_use_tokens + grounding_tokens
                            )
                            output_text_tokens = (
                                candidates_tokens - thinking_and_tool_tokens
                            )

                            usage_parts.append(f"输入：{prompt_tokens}")
                            if output_text_tokens > 0:
                                usage_parts.append(f"输出：{output_text_tokens}")
                            if thinking_and_tool_tokens > 0:
                                usage_parts.append(
                                    f"思考/工具：{thinking_and_tool_tokens}"
                                )
                            usage_parts.append(f"总计：{total_tokens}")

                            usage_msg = (
                                f"Token 用量：{', '.join(usage_parts)}"
                                if usage_parts
                                else "用量信息可用"
                            )
                            # 不再频繁 log，避免刷屏，仅发送状态
                            # logger.info(usage_msg) 
                            await self.emit_status(usage_msg, done=False)
                        # --- 结束 Token 计算 ---

                        if finish_reason := chunk.get("candidates", [{}])[0].get(
                            "finishReason"
                        ):
                            logger.info(f"API 完成原因：{finish_reason}")
                            finish_reason_received = True

                    except json.JSONDecodeError:
                        logger.warning(f"解码 JSON 行失败：{line}")
                    except (KeyError, IndexError) as e:
                        logger.debug(f"数据块解析错误：{e}")

                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    error_msg = f"🚨 流超时：{self.valves.stream_idle_timeout}秒无数据。"
                    logger.error(error_msg)
                    await self.emit_status(error_msg, done=True)
                    yield error_msg
                    return

        finally:
            if not finish_reason_received and content_yielded:
                logger.warning("流结束但未收到 finishReason。")

    async def get_request_stream(
        self, messages: list, model_name: str
    ) -> AsyncGenerator[str, None]:
        """构建请求并从 Gemini API 流式传输响应。"""
        api_model = self.valves.api_model
        
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
                        if image_url.startswith("data:image") and ";base64," in image_url:
                            try:
                                header, encoded_data = image_url.split(",", 1)
                                mime_type = header.split(":", 1)[1].split(";", 1)[0]
                                parts.append({
                                    "inlineData": {
                                        "mimeType": mime_type,
                                        "data": encoded_data
                                    }
                                })
                            except Exception:
                                pass
            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        # 如果最后一条是 model，补一个 user continue (这是 API 的要求，不能以 model 结尾)
        if gemini_contents and gemini_contents[-1]["role"] == "model":
            gemini_contents.append({"role": "user", "parts": [{"text": "Continue"}]})

        gemini_tools = [{"googleSearch": {}}, {"code_execution": {}}]

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
                async with client.stream("POST", url, json=data) as response:
                    if response.status_code != 200:
                        error_content = await response.aread()
                        error_message = f"🚨 API 错误：{response.status_code} - {error_content.decode()}"
                        yield error_message
                        return

                    async for content in self.process_stream(response):
                        yield content

        except Exception as e:
            error_msg = f"🚨 请求异常：{e}"
            logger.exception(error_msg)
            yield error_msg

    async def check_completion(self, messages: list, last_response: str) -> bool:
        """
        使用模型独立判断最后的回复是否完整。
        """
        # 提取最后一条用户消息作为上下文
        last_user_msg = "N/A"
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content")
                if isinstance(content, str):
                    last_user_msg = content
                elif isinstance(content, list):
                    # 简化处理，只取文本部分
                    texts = [p.get("text", "") for p in content if p.get("type") == "text"]
                    last_user_msg = " ".join(texts)
                break
        
        # 构造判断提示词
        judge_prompt = f"""
You are a strict output validator.
Your task is to analyze the following response from an AI model corresponding to the user's request and determine if the response is COMPLETE or INCOMPLETE.

User Request (Context):
"{last_user_msg[:2000]}" ... (truncated)

Model Response to Evaluate:
"{last_response}"

Criteria:
1. Does the response finish its sentence?
2. Does it seem to abruptly stop?
3. Does it fully address the request or is it clearly cut off?

Reply ONLY with the word "COMPLETE" if it is finished, or "INCOMPLETE" if it needs to continue. Do not output anything else.
"""
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": judge_prompt}]}],
            "generationConfig": {
                "temperature": 0.0, # 确定性输出
                "maxOutputTokens": 10
            }
        }
        
        # 使用 fast/lite 模型进行判断，或者复用当前模型
        judge_model = self.valves.api_model 
        url = f"/v1beta/models/{judge_model}:generateContent?key={self.valves.api_key}"

        try:
            async with httpx.AsyncClient(base_url=self.valves.base_url, trust_env=True, timeout=30) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip().upper()
                    logger.info(f"🔍 完整性检查结果：{text}")
                    return "COMPLETE" in text
                else:
                    logger.warning(f"完整性检查失败 ({response.status_code})，默认认为已完成以防止死循环。")
                    return True
        except Exception as e:
            logger.error(f"完整性检查发生异常：{e}，默认为 True")
            return True

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        self.emitter = __event_emitter__
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] 开始处理请求。")

        try:
            if not self.valves.api_key:
                yield "❌ 错误：未设置 API 密钥。"
                return

            messages = body.get("messages", [])
            model_id = body.get("model", self.valves.model_id)

            loop_count = 0
            max_loops = 15 # 安全上限
            
            while loop_count < max_loops:
                loop_count += 1
                stream_had_error = False
                full_response_this_turn = ""
                
                # 1. 执行流式生成
                async for chunk in self.get_request_stream(messages, model_id):
                    if chunk.startswith("🚨"):
                        stream_had_error = True
                        yield chunk
                        continue

                    full_response_this_turn += chunk

                    # 根据配置输出 (块状/字符/空格)
                    if self.valves.block_size > 1:
                        for part in self.split_html_tags(chunk):
                            if part.startswith('<') and part.endswith('>'):
                                yield part
                            else:
                                for i in range(0, len(part), self.valves.block_size):
                                    yield part[i:i + self.valves.block_size]
                                    if self.valves.output_delay > 0: await asyncio.sleep(self.valves.output_delay)
                    elif self.valves.block_size < 0:
                        for part in self.split_html_tags(chunk):
                            if part.startswith('<') and part.endswith('>'):
                                yield part
                            else:
                                for word in part.split():
                                    yield word + ' '
                                    if self.valves.output_delay > 0: await asyncio.sleep(self.valves.output_delay)
                    else:
                        for char in chunk:
                            yield char
                            if self.valves.output_delay > 0 and char not in ['<', '>']:
                                await asyncio.sleep(self.valves.output_delay)

                if stream_had_error:
                    break
                
                if not full_response_this_turn.strip():
                    logger.warning("收到空响应，停止生成。")
                    break

                # 2. 独立判断是否结束
                # 等待流稍微稳定
                await asyncio.sleep(0.2)
                await self.emit_status(f"正在验证回答完整性... (第 {loop_count} 轮)", done=False)
                
                is_complete = await self.check_completion(messages, full_response_this_turn)

                if is_complete:
                    logger.info(f"[{request_id}] 判定回答已完整。")
                    break
                else:
                    logger.info(f"[{request_id}] 判定回答不完整，准备继续...")
                    await self.emit_status(f"检测到回答未完成，自动继续生成... (第 {loop_count + 1} 轮)", done=False)
                    
                    # 更新历史
                    messages.append({"role": "model", "content": full_response_this_turn})
                    messages.append({"role": "user", "content": "Please continue strictly from where you stopped."})
                    
                    # 发送换行符以分隔接下来的内容
                    yield "\n" 

            if loop_count >= max_loops:
                yield "\n\n[达到最大自动续写次数限制]"

            await self.emit_status("生成完成。", done=True)

        except Exception as e:
            logger.exception(f"[{request_id}] 致命错误：{e}")
            yield f"❌ 系统错误：{e}"