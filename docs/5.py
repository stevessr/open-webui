"""
title: OpenRouter xAI Grok 4.1 Pure Pipe
author: Open WebUI User
version: 0.4.0
license: MIT
description: 强制使用 Grok 4.1 原生 Tools 格式 (Web Search, X Search, Code Interpreter)。
"""

import requests
import json
from typing import List, Union, Generator, Iterator
from pydantic import BaseModel, Field

class Pipe:
    class Valves(BaseModel):
        # --- 基础配置 ---
        OPENROUTER_API_KEY: str = Field(
            default="", 
            description="OpenRouter API Key (sk-or-...)"
        )
        MODEL_ID: str = Field(
            default="x-ai/grok-4-1-fast", 
            description="OpenRouter 模型 ID (如 x-ai/grok-4.1-fast)"
        )
        
        YOUR_SITE_URL: str = Field(default="https://openwebui.com", description="Site URL")
        YOUR_SITE_NAME: str = Field(default="Open WebUI", description="Site Name")

    class UserValves(BaseModel):
        # --- 工具开关 (直接映射到 xAI Tools) ---
        ENABLE_WEB_SEARCH: bool = Field(
            default=False, 
            description="开启 Web Search (互联网搜索)"
        )
        ENABLE_X_SEARCH: bool = Field(
            default=False, 
            description="开启 X Search (X/Twitter 帖子搜索)"
        )
        ENABLE_CODE_INTERPRETER: bool = Field(
            default=False, 
            description="开启 Code Interpreter (代码解释器)"
        )
        
        # --- 高级工具配置 ---
        FILE_SEARCH_COLLECTION_IDS: str = Field(
            default="", 
            description="File Search 集合 ID (逗号分隔，例如 id1,id2)"
        )
        MCP_SERVER_URL: str = Field(
            default="", 
            description="MCP Server URL (例如 https://your-mcp-server)"
        )

        # --- 调试与参数 ---
        DEBUG_ERROR: bool = Field(
            default=True, 
            description="若 API 报错，在对话框显示详细 JSON 错误信息"
        )
        TEMPERATURE: float = Field(default=0.6, description="Temperature")
        MAX_TOKENS: int = Field(default=4096, description="Max Tokens")
        

    def __init__(self):
        self.type = "manifold"
        self.id = "openrouter_grok_pure"
        self.name = "OR: "
        self.valves = self.Valves()
        self.uservalues = self.UserValves()

    def get_openrouter_models(self):
        return [
            {"id": "grok-4.1-tools", "name": "Grok 4.1 Fast (Tools)"},
        ]

    def pipe(self, body: dict, __user__: dict = None) -> Union[str, Generator, Iterator]:
        self.uservalues = __user__.get("valves") if __user__ else self.UserValves()
        api_key = self.valves.OPENROUTER_API_KEY
        if not api_key:
            return "Error: OPENROUTER_API_KEY not set."

        # 1. 基础 Payload
        messages = body.get("messages", [])
        
        payload = {
            "model": self.valves.MODEL_ID,
            "messages": messages,
            "stream": True,
            "temperature": self.uservalues.TEMPERATURE,
            "max_tokens": self.uservalues.MAX_TOKENS,
            "include_reasoning": True # 请求 OpenRouter 返回思维链
        }

        # 2. 构建 xAI Tools 数组 (严格遵循文档格式)
        xai_tools = []

        if self.uservalues.ENABLE_WEB_SEARCH:
            xai_tools.append({"type": "web_search"})
        
        if self.uservalues.ENABLE_X_SEARCH:
            xai_tools.append({"type": "x_search"})
            
        if self.uservalues.ENABLE_CODE_INTERPRETER:
            xai_tools.append({"type": "code_interpreter"})

        # 处理 File Search
        if self.uservalues.FILE_SEARCH_COLLECTION_IDS:
            ids = [x.strip() for x in self.uservalues.FILE_SEARCH_COLLECTION_IDS.split(",") if x.strip()]
            if ids:
                xai_tools.append({
                    "type": "file_search",
                    "collection_ids": ids
                })

        # 处理 MCP
        if self.uservalues.MCP_SERVER_URL:
            xai_tools.append({
                "type": "mcp",
                "server_url": self.uservalues.MCP_SERVER_URL
            })

        # 仅在有工具启用时添加 tools 字段
        if xai_tools:
            payload["tools"] = xai_tools

        # 3. 请求头
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.valves.YOUR_SITE_URL,
            "X-Title": self.valves.YOUR_SITE_NAME,
        }

        url = "https://openrouter.ai/api/v1/chat/completions"

        try:
            req = requests.post(url, headers=headers, json=payload, stream=True)
            
            # --- 错误处理逻辑 ---
            if req.status_code >= 400:
                error_msg = f"Error {req.status_code}: "
                try:
                    error_json = req.json()
                    # 格式化 JSON 错误信息以便阅读
                    error_msg += "\n" + json.dumps(error_json, indent=2, ensure_ascii=False)
                except:
                    error_msg += req.text
                
                if self.uservalues.DEBUG_ERROR:
                    # 使用 Markdown 代码块显示错误，防止格式混乱
                    return f"```json\n{error_msg}\n```"
                else:
                    return f"API Error: {req.status_code}. Check logs or enable DEBUG_ERROR."

            req.raise_for_status()

            # --- 流式响应处理 ---
            def stream_generator():
                for line in req.iter_lines():
                    if line:
                        line = line.decode("utf-8")
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                choice = data.get("choices", [{}])[0]
                                delta = choice.get("delta", {})
                                
                                content = delta.get("content", "")
                                # 兼容不同字段名的 reasoning
                                reasoning = delta.get("reasoning", "") or delta.get("reasoning_content", "")
                                
                                if reasoning:
                                    yield f"<think>{reasoning}</think>"
                                if content:
                                    yield content
                            except json.JSONDecodeError:
                                pass
            return stream_generator()

        except requests.exceptions.RequestException as e:
            return f"Request Failed: {e}"