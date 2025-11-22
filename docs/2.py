"""
title: Gemini with search & code (Pseudo-streaming) - Robust Version with Detailed Token Calculation
licence: MIT
"""

import json
import logging
import time
import uuid
import re
import base64
from typing import AsyncIterable, Optional, Callable, Awaitable, AsyncGenerator, List
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
    该管道处理流式响应并提供状态更新，支持独立的文件上传配置（URL 和 API Key）。
    """

    class Valves(BaseModel):
        # --- 基础 API 配置 (用于对话生成) ---
        base_url: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Gemini 生成 API 的基础 URL (用于 chat/generateContent)。",
        )
        api_key: str = Field(default="", description="用于对话生成的 Gemini API 密钥。")

        # --- 文件上传 API 配置 (独立) ---
        file_api_base_url: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Gemini 文件上传 API 的基础 URL (用于 upload/files)。",
        )
        file_api_key: str = Field(
            default="",
            description="用于文件上传的 Gemini API 密钥。如果留空，将默认使用上面的 api_key。",
        )

        timeout: int = Field(default=600, description="整个请求的超时时间（秒）")

        # --- 流式和超时配置 ---
        stream_idle_timeout: int = Field(
            default=30, description="在假定连接中断之前，等待新数据的最长时间（秒）。"
        )

        # --- 模型配置 ---
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
        self.uservalues = self.UserValves()
        self.emitter: Optional[Callable[[dict], Awaitable[None]]] = None
        logger.info(f"管道 '{self.name}' 已初始化。")

    async def emit_status(self, message: str, done: bool = False):
        if self.emitter:
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
        """
        pattern = r"(<[^>]+>)"
        return re.split(pattern, text)

    async def _upload_file(
        self, client: httpx.AsyncClient, mime_type: str, data: bytes
    ) -> str:
        """
        使用 Gemini File API 的可恢复上传协议上传文件字节。
        使用 self.valves.file_api_base_url 和 self.valves.file_api_key。
        """
        num_bytes = len(data)
        display_name = "Uploaded Image"

        # 1. 确定使用的 API Key (优先使用独立的上传 Key，没有则回退到主 Key)
        upload_api_key = (
            self.valves.file_api_key
            if self.valves.file_api_key
            else self.valves.api_key
        )

        if not upload_api_key:
            raise ValueError("未设置上传用的 API Key (file_api_key 或 api_key 均为空)")

        # 2. 构造上传初始 URL
        base_upload_url = self.valves.file_api_base_url.rstrip("/")
        if not base_upload_url:
            base_upload_url = "https://generativelanguage.googleapis.com"

        # 简单的路径拼接，确保指向 /upload/v1beta/files
        if base_upload_url.endswith("/upload/v1beta/files"):
            upload_endpoint = base_upload_url
        else:
            upload_endpoint = f"{base_upload_url}/upload/v1beta/files"

        params = {"key": upload_api_key}

        headers_init = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(num_bytes),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json",
        }

        payload_init = {"file": {"display_name": display_name}}

        logger.info(
            f"开始上传文件 ({num_bytes} bytes, {mime_type}) 到：{upload_endpoint}"
        )

        try:
            resp_init = await client.post(
                upload_endpoint, params=params, headers=headers_init, json=payload_init
            )
            resp_init.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"上传初始化失败：{e.response.text}")
            raise e

        # 从响应头获取实际的上传 URL
        upload_url = resp_init.headers.get("x-goog-upload-url")
        if not upload_url:
            raise ValueError("未从 API 收到 x-goog-upload-url")

        # 3. 上传实际字节
        headers_upload = {
            "Content-Length": str(num_bytes),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize",
        }

        # 注意：upload_url 通常是一个完整的绝对路径，httpx 会直接使用它
        resp_upload = await client.post(
            upload_url, headers=headers_upload, content=data
        )
        resp_upload.raise_for_status()

        file_info = resp_upload.json()
        file_uri = file_info.get("file", {}).get("uri")

        if not file_uri:
            raise ValueError("上传完成但未收到 file_uri")

        logger.info(f"文件上传成功：{file_uri}")
        return file_uri

    async def process_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[str, None]:
        """处理来自 Gemini API 的服务器发送事件 (SSE) 流。"""
        logger.info("开始处理 API 响应流。")
        finish_reason_received = False
        stream_iterator = response.aiter_lines()
        content_yielded = False
        is_thinking = False

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

                                        if not text_content:
                                            continue

                                        content_yielded = True

                                        if is_thought_part:
                                            prefix = ""
                                            if not is_thinking:
                                                prefix = "<think>"
                                                is_thinking = True

                                            quoted_lines = [
                                                f"> {line}"
                                                for line in text_content.splitlines()
                                            ]
                                            quoted_thought = "\n".join(quoted_lines)

                                            if text_content.endswith("\n"):
                                                quoted_thought += "\n"

                                            if (
                                                not quoted_thought
                                                and text_content.strip() == ""
                                            ):
                                                quoted_thought = text_content

                                            yield prefix + quoted_thought

                                        else:
                                            prefix = ""
                                            if is_thinking:
                                                prefix = "</think>"
                                                is_thinking = False

                                            yield prefix + text_content

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
                                usage_parts.append(f"输出 (内容): {output_text_tokens}")

                            if thinking_and_tool_tokens > 0:
                                usage_parts.append(
                                    f"输出 (思考/工具): {thinking_and_tool_tokens}"
                                )

                            usage_parts.append(f"总计：{total_tokens}")

                            usage_msg = (
                                f"Token 用量：{', '.join(usage_parts)}"
                                if usage_parts
                                else "用量信息可用"
                            )
                            logger.debug(usage_msg)
                            await self.emit_status(usage_msg, done=False)

                        if finish_reason := chunk.get("candidates", [{}])[0].get(
                            "finishReason"
                        ):
                            logger.info(f"从 API 收到完成原因：{finish_reason}")
                            finish_reason_received = True

                    except json.JSONDecodeError:
                        logger.warning(f"解码 JSON 行失败：{line}. 跳过此行。")
                    except Exception as e:
                        logger.debug(f"处理数据块错误：{e}. 跳过此块。")

                except StopAsyncIteration:
                    logger.info("响应流正常结束。")
                    break
                except asyncio.TimeoutError:
                    error_msg = f"🚨 流超时：在 {self.valves.stream_idle_timeout} 秒内未收到新数据。"
                    logger.error(error_msg)
                    await self.emit_status(error_msg, done=True)
                    yield error_msg
                    return

            if is_thinking:
                yield "</think>"
                is_thinking = False

        finally:
            if not finish_reason_received and not content_yielded:
                logger.warning("流结束但未收到完成信号。")

    async def get_request_stream(
        self, messages: list, model_name: str
    ) -> AsyncGenerator[str, None]:
        """构建请求并从 Gemini API 流式传输响应，支持通过 File API 上传图片。"""
        api_model = self.valves.api_model
        logger.info(
            f"为 UI 模型 '{model_name}' 准备请求，使用 API 模型 '{api_model}'。"
        )

        gemini_contents = []

        # 使用独立的 httpx Client 进行上传操作
        async with httpx.AsyncClient(timeout=self.valves.timeout) as upload_client:
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

                            mime_type = "image/jpeg"  # 默认
                            image_bytes = None

                            # 1. 处理 Data URI
                            if image_url.startswith("data:image"):
                                try:
                                    header, encoded_data = image_url.split(",", 1)
                                    mime_type = header.split(":", 1)[1].split(";", 1)[0]
                                    image_bytes = base64.b64decode(encoded_data)
                                except Exception as e:
                                    logger.error(f"解析 base64 图片数据失败：{e}")
                                    await self.emit_status(
                                        "警告：解析图片数据失败，已跳过图片。",
                                        done=False,
                                    )

                            # 2. 处理远程 URL
                            elif image_url.startswith(
                                "http://"
                            ) or image_url.startswith("https://"):
                                if self.valves.file_api_key == "":
                                    await self.emit_status(
                                        "警告：未配置上传 API Key，无法上传远程图片，已跳过图片。",
                                        done=False,
                                    )
                                    continue
                                try:
                                    await self.emit_status(
                                        f"正在下载远程图片...", done=False
                                    )
                                    resp = await upload_client.get(image_url)
                                    if resp.status_code == 200:
                                        image_bytes = resp.content
                                        import mimetypes

                                        guessed_type, _ = mimetypes.guess_type(
                                            image_url
                                        )
                                        if guessed_type:
                                            mime_type = guessed_type
                                    else:
                                        logger.error(
                                            f"下载远程图片失败：{resp.status_code}"
                                        )
                                except Exception as e:
                                    logger.error(f"下载远程图片异常：{e}")

                            # 3. 执行上传
                            if image_bytes:
                                try:
                                    await self.emit_status(
                                        "正在上传图片到 Gemini...", done=False
                                    )
                                    file_uri = await self._upload_file(
                                        upload_client, mime_type, image_bytes
                                    )

                                    parts.append(
                                        {
                                            "file_data": {
                                                "mime_type": mime_type,
                                                "file_uri": file_uri,
                                            }
                                        }
                                    )
                                except Exception as e:
                                    error_msg = f"上传图片到 Gemini 失败：{e}"
                                    logger.error(error_msg)
                                    await self.emit_status(
                                        f"警告：{error_msg}", done=False
                                    )

                if parts:
                    gemini_contents.append({"role": role, "parts": parts})

        if gemini_contents and gemini_contents[-1]["role"] == "model":
            gemini_contents.append({"role": "user", "parts": [{"text": "Continue"}]})

        gemini_tools = [
            {"googleSearch": {}},
            {"code_execution": {}},
        ]

        data = {
            "contents": gemini_contents,
            "tools": gemini_tools,
            "generationConfig": {
                "temperature": self.uservalves.temperature,
                "topP": self.uservalves.top_p,
                "thinkingConfig": {
                    "includeThoughts": self.uservalves.include_thoughts,
                    "thinkingBudget": self.uservalves.thinking_budget,
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
            error_msg = f"🚨 连接错误：无法连接到 {self.valves.base_url}。 {e}"
            logger.exception(error_msg)
            await self.emit_status(error_msg, done=True)
            yield error_msg
        except httpx.TimeoutException:
            error_msg = f"🚨 请求超时：{self.valves.timeout} 秒超时。"
            logger.error(error_msg)
            await self.emit_status(error_msg, done=True)
            yield error_msg
        except Exception as e:
            error_msg = f"🚨 发生意外错误：{e}"
            logger.exception(error_msg)
            await self.emit_status(error_msg, done=True)
            yield error_msg

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        """管道的主入口点。"""
        self.emitter = __event_emitter__
        self.uservalues = __user__.get("valves") if __user__ else self.UserValves()
        request_id = str(uuid.uuid4())
        logger.info(f"[{request_id}] 管道开始处理新请求。")

        try:
            if not self.valves.api_key:
                error_msg = "❌ 错误：Gemini API 密钥未设置。"
                yield error_msg
                await self.emit_status(error_msg, done=True)
                return

            messages = body.get("messages")
            model_id = body.get("model", self.valves.model_id)

            async for chunk in self.get_request_stream(messages, model_id):
                # 处理输出模式（分块/字符）
                if self.uservalves.block_size > 1:
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            yield chunk_part
                        else:
                            for i in range(
                                0, len(chunk_part), self.uservalves.block_size
                            ):
                                block = chunk_part[i : i + self.uservalves.block_size]
                                if block:
                                    yield block
                                    if self.uservalves.output_delay > 0:
                                        await asyncio.sleep(
                                            self.uservalves.output_delay
                                        )
                elif self.uservalves.block_size < 0:
                    # 按空格分块
                    for chunk_part in self.split_html_tags(chunk):
                        if chunk_part.startswith("<") and chunk_part.endswith(">"):
                            yield chunk_part
                        else:
                            parts = re.split(r"(\s+)", chunk_part)
                            for part in parts:
                                if part:
                                    yield part
                                    if self.uservalves.output_delay > 0:
                                        await asyncio.sleep(
                                            self.uservalves.output_delay
                                        )
                else:
                    # 逐字输出
                    skip = False
                    for char in chunk:
                        yield char
                        if char == "<":
                            skip = True
                        elif char == ">":
                            skip = False
                        if skip:
                            continue
                        if self.uservalves.output_delay > 0:
                            await asyncio.sleep(self.uservalves.output_delay)

            await self.emit_status("生成完成。", done=True)

        except Exception as e:
            error_msg = f"❌ 系统错误：{e}"
            logger.exception(f"[{request_id}] {error_msg}")
            await self.emit_status(f"致命错误：{e}", done=True)
            yield error_msg
