"""
title: Gemini 5-Step Agent (Clean Output)
licence: MIT
author: OpenWebUI User
description: Forces Gemini to follow a strict 5-step reasoning loop. Fixed async generator return error and removed redundant headers.
"""

import json
import logging
import re
import asyncio
from typing import Optional, Callable, Awaitable, AsyncGenerator, List
import httpx
from pydantic import BaseModel, Field

# --- 日志配置 ---
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
    Gemini 5-Step Agent Pipe - V3.3 Clean
    流程：Plan -> Act 1 -> Review -> Act 2 -> Summarize
    优化：删除了聊天气泡中的阶段标题文本，只保留状态栏显示。
    """

    class Valves(BaseModel):
        base_url: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Gemini API 的基础 URL",
        )
        api_key: str = Field(default="", description="Gemini API 密钥")
        timeout: int = Field(default=600, description="整个请求的超时时间（秒）")

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
            default=False,
            description="是否显示原生 API 的思考标签（建议 False，以免混淆）。",
        )
        output_delay: float = Field(
            default=0.01,
            description="打字机效果延迟（秒）。",
        )

        # 续写/Token 配置
        max_step_continuation: int = Field(
            default=3,
            description="每个步骤（如 Act 1）内部最大允许的自动续写次数（防止单步截断）。",
        )
        max_output_tokens: int = Field(
            default=8192, description="单次请求最大 Token 数"
        )
        temperature: float = Field(default=0.7)
        top_p: float = Field(default=0.9)

    def __init__(self):
        self.type = "manifold"
        self.name = "Gemini 5-Step Agent Clean"
        self.valves = self.Valves()
        self.emitter: Optional[Callable[[dict], Awaitable[None]]] = None
        self.last_finish_reason = None

    async def emit_status(self, message: str, done: bool = False):
        """发送状态更新给 UI"""
        if self.emitter:
            clean_msg = message[:300] + "..." if len(message) > 300 else message
            await self.emitter(
                {
                    "type": "status",
                    "data": {"description": clean_msg, "done": done},
                }
            )

    def get_models(self) -> List[dict]:
        return [{"id": self.valves.model_id, "name": self.valves.model_display_name}]

    def pipes(self) -> List[dict]:
        return self.get_models()

    async def process_stream(
        self, response: httpx.Response
    ) -> AsyncGenerator[str, None]:
        """处理 SSE 流"""
        self.last_finish_reason = None

        async for line in response.aiter_lines():
            if not line.strip() or not line.startswith("data: "):
                continue
            line = line[6:]
            if line == "[DONE]":
                break
            try:
                chunk = json.loads(line)
                if "error" in chunk:
                    err_msg = chunk.get("error", {}).get("message", "Unknown Error")
                    yield f"🚨 API Error: {err_msg}"
                    return

                if "candidates" in chunk:
                    candidate = chunk["candidates"][0]
                    if "finishReason" in candidate:
                        self.last_finish_reason = candidate["finishReason"]

                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            text_content = part.get("text", "")
                            is_thought = part.get("thought", False)

                            if text_content:
                                if is_thought and self.valves.include_thoughts:
                                    yield f"\n<think>{text_content}</think>\n"
                                elif not is_thought:
                                    yield text_content

            except Exception as e:
                logger.error(f"Stream processing error: {e}")

    async def get_request_stream(self, messages: list) -> AsyncGenerator[str, None]:
        """构造请求并发起流式调用"""

        gemini_contents = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            parts = [{"text": str(msg.get("content", ""))}]
            if parts:
                gemini_contents.append({"role": role, "parts": parts})

        if gemini_contents and gemini_contents[-1]["role"] == "model":
            gemini_contents.append(
                {"role": "user", "parts": [{"text": "Please continue."}]}
            )

        payload = {
            "contents": gemini_contents,
            "tools": [
                {"googleSearch": {}},
                {"code_execution": {}},
                {"url_context": {}},
            ],
            "generationConfig": {
                "temperature": self.valves.temperature,
                "topP": self.valves.top_p,
                "maxOutputTokens": self.valves.max_output_tokens,
            },
        }

        if self.valves.thinking_budget != 0:
            payload["generationConfig"]["thinkingConfig"] = {
                "includeThoughts": self.valves.include_thoughts,
                "thinkingBudget": self.valves.thinking_budget,
            }

        url = f"/v1beta/models/{self.valves.api_model}:streamGenerateContent?key={self.valves.api_key}&alt=sse"

        try:
            async with httpx.AsyncClient(
                base_url=self.valves.base_url, timeout=self.valves.timeout
            ) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err = await response.aread()
                        yield f"🚨 HTTP {response.status_code}: {err.decode()}"
                        return
                    async for chunk in self.process_stream(response):
                        yield chunk
        except Exception as e:
            yield f"🚨 Connection Error: {e}"

    # --- 核心：单步执行逻辑 ---
    async def execute_step(
        self, step_name: str, step_prompt: str, context_messages: list
    ) -> AsyncGenerator[str, None]:
        """
        执行 5 步中的某一步。
        """

        current_messages = context_messages.copy()

        current_messages.append(
            {
                "role": "user",
                "content": f"**Current Task: {step_name}**\nInstructions: {step_prompt}\n\nProvide your output for this step now.",
            }
        )

        loop_count = 0

        # 【修改点 1】移除了此处的 yield f"\n\n### 🟢 {step_name}\n"
        # 这样阶段名称只会显示在 UI 的状态栏中，而不会打印在聊天文本里

        while loop_count < self.valves.max_step_continuation:
            loop_count += 1
            chunk_buffer = ""

            async for chunk in self.get_request_stream(current_messages):
                chunk_buffer += chunk
                # 流式输出给用户
                if self.valves.output_delay > 0:
                    for char in chunk:
                        yield char
                        await asyncio.sleep(self.valves.output_delay / 2)
                else:
                    yield chunk

            # 检查是否需要续写
            if self.last_finish_reason == "MAX_TOKENS":
                await self.emit_status(
                    f"{step_name}: Continuing truncated output...", done=False
                )
                current_messages.append({"role": "model", "content": chunk_buffer})
                current_messages.append({"role": "user", "content": "continue"})
            else:
                break

    async def pipe(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> AsyncGenerator[str, None]:

        self.emitter = __event_emitter__
        messages = body.get("messages", [])

        if not self.valves.api_key:
            yield "Error: API Key not configured."
            return

        steps = [
            (
                "Phase 1: PLAN",
                "Analyze the user's request. Identify the core intent and potential challenges. Create a numbered plan.",
            ),
            (
                "Phase 2: ACT (Initial)",
                "Execute the first steps of your plan. Use tools (Search/Code) if needed. Provide initial results.",
            ),
            (
                "Phase 3: REVIEW",
                "Critically analyze your output from Phase 2. Check for errors, bugs, or missing info.",
            ),
            (
                "Phase 4: ACT (Refinement)",
                "Execute corrections based on the review. Complete the plan.",
            ),
            (
                "Phase 5: SUMMARIZE",
                "Provide the final, polished answer to the user. Synthesize all information. This is the final output.",
            ),
        ]

        internal_history = [msg for msg in messages]

        try:
            total_steps = len(steps)
            for i, (name, prompt) in enumerate(steps):

                await self.emit_status(
                    f"Running {name} ({i+1}/{total_steps})...", done=False
                )

                step_output_buffer = ""  # 用于收集这一步的完整文本

                # 执行该步骤
                async for chunk in self.execute_step(name, prompt, internal_history):
                    if isinstance(chunk, str):
                        yield chunk
                        step_output_buffer += chunk

                # 【修改点 2】优化历史记录
                # 因为我们没有在输出流中打印标题，为了让模型记住它刚做了什么，
                # 我们在存入历史记录时，显式加上标题（用户看不见，但模型看得见）。
                clean_content = step_output_buffer.strip()

                internal_history.append(
                    {"role": "user", "content": f"Instruction for {name}: {prompt}"}
                )
                internal_history.append(
                    {"role": "model", "content": f"**{name} Output:**\n{clean_content}"}
                )

                # 步骤间添加简单的换行，防止文字挤在一起
                yield "\n\n"

            await self.emit_status("All steps completed.", done=True)

        except Exception as e:
            logger.exception(f"Agent Error: {e}")
            yield f"\n\nSystem Error: {str(e)}"
