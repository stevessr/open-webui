"""
title: MCP Client for microsoft_learn
author: stevessr
version: 0.3.0
license: MIT
description: Connects to microsoft_learn
"""

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict

default_url = "https://server.smithery.ai/@microsoft/learn_mcp/mcp"


class EventEmitter:
    """
    Helper to safely emit events to the OpenWebUI frontend.
    """

    def __init__(self, event_emitter: Callable[[dict], Any] = None):
        self.event_emitter = event_emitter

    async def emit(self, description="Unknown State", status="in_progress", done=False):
        if self.event_emitter:
            await self.event_emitter(
                {
                    "type": "status",
                    "data": {
                        "status": status,
                        "description": description,
                        "done": done,
                    },
                }
            )

    async def emit_message(self, content: str):
        if self.event_emitter:
            await self.event_emitter({"type": "message", "data": {"content": content}})


def extract_response_data(response: Any) -> Dict:
    """
    Parses the response, handling both Standard JSON and SSE (Server-Sent Events).
    Smithery often returns JSON wrapped in `data: {...}` lines.
    """
    if response.status_code != 200:
        # Attempt to extract error message from body
        try:
            err = response.json()
            if "error" in err:
                raise Exception(f"HTTP {response.status_code}: {err['error']}")
        except:
            pass
        raise Exception(f"HTTP {response.status_code} Error: {response.text[:200]}")

    # 1. Try Standard JSON
    try:
        return response.json()
    except json.JSONDecodeError:
        pass  # Continue to SSE parsing

    # 2. Parse SSE (text/event-stream)
    text_content = response.text
    for line in text_content.splitlines():
        if line.startswith("data:"):
            json_str = line[5:].strip()  # Remove 'data:' prefix
            try:
                # We found valid JSON in the stream
                return json.loads(json_str)
            except json.JSONDecodeError:
                continue

    # If parsing failed completely
    raise Exception(
        f"Could not parse server response (Invalid JSON/SSE). Raw: {text_content[:200]}..."
    )


# --- Main Tools Class ---


class Tools:
    class Valves(BaseModel):
        MCP_SERVER_URL: str = Field(
            default=default_url,
            description="The MCP Server URL (Smithery/Streamable HTTP supported).",
        )
        MCP_AUTH_TOKEN: str = Field(
            default="",
            description="Optional Bearer token for authentication.",
        )

    class UserValves(BaseModel):
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="Timeout in seconds (default: 300s).",
        )
        DEBUG_MODE: bool = Field(
            default=True,
            description="Log JSON-RPC payloads and errors to the chat.",
        )
        TOOL_INFO_CACHE: str = Field(
            default="",
            description="Cache for discovered tool information.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()
        self.protocol_version = "2024-11-05"
        self.client_name = "OpenWebUI-MCP-Client"
        self.client_version = "1.0.1"

    async def _debugger(self, action: str, **kwargs) -> Any:
        """
        Unified internal processor for Headers, Payloads, and Handshake operations.
        :param action: 'headers', 'payload', or 'handshake'
        :param kwargs: parameters required for the specific action
        """
        
        # --- 1. HEADERS GENERATION ---
        if action == "headers":
            session_id = kwargs.get("session_id")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mcp-Protocol-Version": self.protocol_version,
            }
            if self.valves.MCP_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {self.valves.MCP_AUTH_TOKEN}"
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            return headers

        # --- 2. JSON-RPC PAYLOAD GENERATION ---
        elif action == "payload":
            method = kwargs.get("method")
            params = kwargs.get("params")
            request_id = kwargs.get("request_id", 1)
            
            payload = {"jsonrpc": "2.0", "method": method, "id": request_id}
            if params is not None:
                payload["params"] = params
            return payload

        # --- 3. MCP HANDSHAKE (Connect & Init) ---
        elif action == "handshake":
            emitter = kwargs.get("emitter")
            
            # Recursive call to generate payload
            init_payload = await self._debugger(
                "payload",
                method="initialize",
                params={
                    "protocolVersion": self.protocol_version,
                    "capabilities": {"roots": {"listChanged": True}, "sampling": {}},
                    "clientInfo": {
                        "name": self.client_name,
                        "version": self.client_version,
                    },
                }
            )

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Initializing handshake with {self.valves.MCP_SERVER_URL}..."
                )

            try:
                # Recursive call to get base headers
                base_headers = await self._debugger("headers")
                
                response = requests.post(
                    self.valves.MCP_SERVER_URL,
                    headers=base_headers,
                    json=init_payload,
                    timeout=30,
                )

                data = extract_response_data(response)

                # Streamable HTTP servers return session ID in headers
                session_id = response.headers.get("Mcp-Session-Id")

                # Fallback to body if not in headers
                if not session_id:
                    session_id = data.get("result", {}).get("sessionId")

                if "error" in data:
                    raise Exception(f"MCP Initialize Error: {data['error']}")

                server_info = data.get("result", {}).get("serverInfo", {})
                server_name = server_info.get("name", "Unknown Server")

                if self.user_valves.DEBUG_MODE:
                    await emitter.emit_message(
                        f"DEBUG: Handshake Success. Server: {server_name}, Session: {session_id}"
                    )

                await emitter.emit(f"Connected to: {server_name}")

                if session_id:
                    # Recursive call for notification payload & headers with session
                    notify_payload = await self._debugger(
                        "payload", 
                        method="notifications/initialized"
                    )
                    session_headers = await self._debugger("headers", session_id=session_id)
                    
                    requests.post(
                        self.valves.MCP_SERVER_URL,
                        headers=session_headers,
                        json=notify_payload,
                        timeout=10,
                    )

                return session_id

            except Exception as e:
                raise Exception(f"Handshake failed: {str(e)}")
        
        else:
            raise ValueError(f"Unknown _debugger action: {action}")

    async def microsoft_learn_info(
        self, __event_emitter__: Callable[[dict], Any] = None, __user__: Dict = None
    ) -> str:
        """
        get microsoft_learn tool latest information.
        """
        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Connecting to MCP Server...")

        try:
            # Use Unified Debugger for Handshake
            session_id = await self._debugger("handshake", emitter=emitter)

            # Use Unified Debugger for Payload
            list_payload = await self._debugger("payload", method="tools/list", params={}, request_id=2)

            await emitter.emit(f"Refreshing Description...")

            # Use Unified Debugger for Headers
            headers = await self._debugger("headers", session_id=session_id)

            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=headers,
                json=list_payload,
                timeout=60,
            )

            result = extract_response_data(response)

            if "error" in result:
                return json.dumps({"error": result["error"]})

            tools = result.get("result", {}).get("tools", [])

            tool_summaries = []
            for tool in tools:
                tool_summaries.append(
                    {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "input_schema": tool.get("inputSchema", {}),
                    }
                )

            await emitter.emit(
                status="complete", description=f"Found {len(tools)} tools", done=True
            )
            self.user_valves.TOOL_INFO_CACHE = json.dumps(
                tool_summaries, ensure_ascii=False, indent=2
            )
            return self.user_valves.TOOL_INFO_CACHE

        except Exception as e:
            await emitter.emit(status="error", description=str(e), done=True)
            return json.dumps({"error": f"Discovery failed: {str(e)}"})

    async def microsoft_learn_tools(
        self,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        list all available tools for microsoft_learn
        """
        if __user__ and "valves" in __user__:
            self.user_valves = __user__["valves"]

        return (
            self.user_valves.TOOL_INFO_CACHE
            if self.user_valves.TOOL_INFO_CACHE != ""
            else "please call refresh_description first."
        )

    async def microsoft_learn_exec(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Execute a specific tool on microsoft_learn with given arguments.
        """
        if __user__ and "valves" in __user__:
            self.user_valves = __user__["valves"]

        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Calling tool: {tool_name}...")

        try:
            # Use Unified Debugger for Handshake
            session_id = await self._debugger("handshake", emitter=emitter)

            # Use Unified Debugger for Payload
            call_payload = await self._debugger(
                "payload", 
                method="tools/call", 
                params={"name": tool_name, "arguments": arguments}, 
                request_id=3
            )

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Calling {tool_name} with {json.dumps(arguments)}"
                )

            # Use Unified Debugger for Headers
            headers = await self._debugger("headers", session_id=session_id)

            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=headers,
                json=call_payload,
                timeout=self.user_valves.REQUEST_TIMEOUT,
            )

            data = extract_response_data(response)

            if "error" in data:
                await emitter.emit(
                    status="error",
                    description=f"Tool Error: {data['error'].get('message')}",
                    done=True,
                )
                return json.dumps({"error": data["error"]})

            content = data.get("result", {}).get("content", [])

            text_results = []
            for item in content:
                if item.get("type") == "text":
                    text_results.append(item.get("text"))
                elif item.get("type") == "resource":
                    text_results.append(
                        f"[Resource: {item.get('resource', {}).get('uri')}]"
                    )
                elif item.get("type") == "image":
                    text_results.append(f"[Image: {item.get('mimeType')}]")

            final_output = "\n".join(text_results)

            await emitter.emit(
                status="complete", description="Tool executed", done=True
            )
            return final_output if final_output else json.dumps(data)

        except Exception as e:
            await emitter.emit(
                status="error", description=f"Execution failed: {str(e)}", done=True
            )
            return json.dumps({"error": str(e)})