"""
title: Gemini 3 Pro (Thinking Level Support)
licence: MIT
"""

import json
import logging
import re
from typing import Optional, Callable, Awaitable, AsyncGenerator, List, Literal
import asyncio

import httpx
from pydantic import BaseModel, Field

try:
    from open_webui.env import SRC_LOG_LEVELS

    log_level = SRC_LOG_LEVELS["MAIN"]
except ImportError:
    log_level = logging.INFO

logging.basicConfig(
    level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)
logger.setLevel(log_level)


class Pipe:
    """
    适配 Gemini 3 Pro Preview 的管道。
    - 修复了流式输出重复/爆炸的问题 (状态机处理 <think> 标签)。
    - 支持通过 Filter 前端选择 Thinking Level (LOW/HIGH)。
    """

    class Valves(BaseModel):
        base_url: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Gemini API 基础 URL",
        )
        api_key: str = Field(default="", description="Gemini API Key")
        model_id: str = Field(
            default="gemini-3-pro",
            description="UI 显示的模型 ID",
        )
        model_display_name: str = Field(
            default="Gemini 3 Pro (Thinking)", description="UI 显示的模型名称"
        )
        api_model: str = Field(
            default="gemini-3-pro-preview",
            description="API 调用的实际模型名称",
        )

    class UserValves(BaseModel):
        temperature: float = Field(default=1, description="Temperature")
        top_p: float = Field(default=0.95, description="Top P")
        include_thoughts: bool = Field(default=True, description="是否显示思考过程")
        output_delay: float = Field(default=0.01, description="输出延迟 (秒)")
        default_thinking_level: Literal["high", "low", "medium"] = Field(
            default="HIGH",
            description="默认思考强度：'LOW' 或 'HIGH'",
        )
        timeout: int = Field(default=600, description="请求超时时间 (秒)")
        stream_idle_timeout: int = Field(default=30, description="流空闲超时时间 (秒)")
        search_tool_enabled: bool = Field(default=True, description="是否启用搜索工具")
        code_execution_tool_enabled: bool = Field(
            default=True, description="是否启用代码执行工具"
        )
        url_context_tool_enabled: bool = Field(
            default=True, description="是否启用 URL 上下文工具"
        )
        google_maps_tool_enabled: bool = Field(
            default=False, description="是否启用 Google 地图工具"
        )

    def __init__(self):
        self.type = "manifold"
        self.name = "gemini3"
        self.valves = self.Valves()
        self.uservalues = self.UserValves()
        self.emitter: Optional[Callable[[dict], Awaitable[None]]] = None

    async def emit_status(self, message: str, done: bool = False):
        if self.emitter:
            await self.emitter(
                {
                    "type": "status",
                    "data": {"description": str(message)[:500], "done": done},
                }
            )

    def pipes(self) -> List[dict]:
        return [{"id": self.valves.model_id, "name": self.valves.model_display_name}]

    async def process_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[str, None]:
        """处理流，使用状态机防止标签爆炸"""
        stream_iterator = response.aiter_lines()

        # 状态变量：记录当前是否在思考块中
        in_thought_block = False

        try:
            while True:
                try:
                    line = await asyncio.wait_for(
                        stream_iterator.__anext__(),
                        timeout=self.uservalues.stream_idle_timeout,
                    )

                    if not line.strip() or not line.startswith("data: "):
                        continue
                    line = line[6:]

                    try:
                        chunk = json.loads(line)

                        # --- Token 统计 ---
                        if usage := chunk.get("usageMetadata"):
                            parts = []
                            if pt := usage.get("promptTokenCount"):
                                parts.append(f"In: {pt}")
                            thoughts = usage.get("thoughtsTokenCount", 0)
                            candidates = usage.get("candidatesTokenCount", 0)
                            if thoughts > 0:
                                parts.append(f"Think: {thoughts}")
                                parts.append(f"Out: {candidates - thoughts}")
                            else:
                                parts.append(f"Out: {candidates}")
                            await self.emit_status(
                                f"Token Usage: {', '.join(parts)}", done=False
                            )

                        # --- 内容处理 ---
                        if "candidates" in chunk:
                            for candidate in chunk.get("candidates", []):
                                if (
                                    "content" in candidate
                                    and "parts" in candidate["content"]
                                ):
                                    for part in candidate["content"]["parts"]:
                                        # 获取当前片段是否为思考内容
                                        is_thought_part = part.get("thought", False)
                                        text_content = part.get("text", "")

                                        if not text_content:
                                            continue

                                        # --- 状态机逻辑 ---
                                        if is_thought_part:
                                            # 如果是思考内容，但还没进入思考块 -> 输出开始标签
                                            if not in_thought_block:
                                                yield "<think>\n"
                                                in_thought_block = True
                                            # 输出纯文本
                                            yield text_content
                                        else:
                                            # 如果是普通内容，但还在思考块里 -> 输出结束标签
                                            if in_thought_block:
                                                yield "\n</think>\n"
                                                in_thought_block = False
                                            # 输出纯文本
                                            yield text_content

                    except json.JSONDecodeError:
                        pass

                except StopAsyncIteration:
                    break
                except asyncio.TimeoutError:
                    yield "🚨 Stream Timeout"
                    return

        finally:
            # 如果流结束时还在思考块中，强制闭合标签
            if in_thought_block:
                yield "\n</think>\n"

    async def get_request_stream(
        self, messages: list, body: dict
    ) -> AsyncGenerator[str, None]:
        api_model = self.valves.api_model

        thinking_params = body.get("thinking_parameters", {})
        thinking_level = thinking_params.get(
            "thinking_level", self.uservalues.default_thinking_level
        )
        thinking_level = thinking_level.upper() if thinking_level else "HIGH"

        tools = body.get("tools", [])

        if not tools:
            # 默认开启搜索，为了增强能力
            tools = []
            if self.uservalues.search_tool_enabled:
                tools.append({"googleSearch": {}})
            if self.uservalues.code_execution_tool_enabled:
                tools.append({"code_execution": {}})
            if self.uservalues.url_context_tool_enabled:
                tools.append({"url_context": {}})
            if self.uservalues.google_maps_tool_enabled:
                tools.append({"googleMaps": {}})

        logger.info(f"Requesting {api_model} with Thinking Level: {thinking_level}")

        gemini_contents = []
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
                        img_url = part.get("image_url", {}).get("url", "")
                        if img_url.startswith("data:image"):
                            parts.append(
                                {
                                    "inline_data": {
                                        "mime_type": "image/jpeg",
                                        "data": img_url.split(",")[1],
                                    }
                                }
                            )

            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        gen_config = {
            "temperature": self.uservalues.temperature,
            "topP": self.uservalues.top_p,
            "thinkingConfig": {
                "includeThoughts": self.uservalues.include_thoughts,
                "thinkingLevel": thinking_level,
            },
        }

        data = {
            "contents": gemini_contents,
            "tools": tools,
            "generationConfig": gen_config,
        }

        url = f"/v1beta/models/{api_model}:streamGenerateContent?key={self.valves.api_key}&alt=sse"

        async with httpx.AsyncClient(
            base_url=self.valves.base_url, timeout=self.uservalues.timeout
        ) as client:
            await self.emit_status(
                f"Calling Gemini 3 (Level: {thinking_level})...", done=False
            )
            try:
                async with client.stream("POST", url, json=data) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        yield f"🚨 API Error {response.status_code}: {err.decode()}"
                        return
                    async for chunk in self.process_stream(response):
                        yield chunk
            except Exception as e:
                yield f"🚨 Connection Error: {e}"

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
        __event_call__: Optional[Callable[[dict], Awaitable[dict]]] = None,
    ) -> AsyncGenerator[str, None]:
        self.emitter = __event_emitter__
        self.uservalues = __user__.get("valves") if __user__ else self.UserValves()

        if not self.valves.api_key:
            yield "❌ API Key Missing"
            return

        messages = body.get("messages", [])

        async for chunk in self.get_request_stream(messages, body):
            yield chunk
            if self.uservalues.output_delay > 0:
                await asyncio.sleep(self.uservalues.output_delay)
