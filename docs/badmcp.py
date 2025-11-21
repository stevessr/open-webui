"""
title: MCP Client (DeepWiki Streamable HTTP)
author: OpenWebUI User
version: 0.4.2
license: MIT
description: Connects to DeepWiki MCP Server using Streamable HTTP (Fixes SSE Parsing & Buffering)
bad: it's too slow
"""

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, Optional, List

# --- Helper Classes & Functions ---


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
    Parses the response for Streamable HTTP.
    Prioritizes standard JSON, handles JSON-L/NDJSON, and strictly parses SSE streams
    (buffering data lines) to handle large multi-line responses.
    """
    if response.status_code not in [200, 202]:
        try:
            err = response.json()
            if "error" in err:
                raise Exception(f"HTTP {response.status_code}: {err['error']}")
        except:
            pass
        raise Exception(f"HTTP {response.status_code} Error: {response.text[:200]}")

    if response.status_code == 202 and not response.text.strip():
        return {}

    # 1. Try standard JSON first (for non-streaming, single-body responses)
    try:
        return response.json()
    except json.JSONDecodeError:
        pass

    # 2. Robust SSE / NDJSON Parsing
    valid_objects = []
    text_content = response.text
    current_data_buffer = []

    for line in text_content.splitlines():
        # SSE lines often start with 'data: ', 'event: ', etc.
        # We shouldn't strip blindly because indentation might matter in JSON,
        # but strict SSE requires 'data:' at the start.
        
        if line.startswith("data:") or line.startswith("data "):
            # Extract content after 'data:' or 'data '
            if line.startswith("data:"):
                content = line[5:]
            else:
                content = line[4:]
            
            # Remove optional leading space (spec allows 'data: value')
            if content.startswith(" "):
                content = content[1:]
            
            current_data_buffer.append(content)
            continue

        # Delimiters: Empty line, or new event/id/retry fields
        is_delimiter = not line.strip() or line.startswith(("event:", "id:", "retry:"))

        if is_delimiter:
            if current_data_buffer:
                # Flush buffer: join all data lines and parse
                full_data = "\n".join(current_data_buffer)
                try:
                    valid_objects.append(json.loads(full_data))
                except json.JSONDecodeError:
                    # If it fails, it might be an intermediate chunk or invalid, ignore
                    pass
                current_data_buffer = []
        else:
            # This line is neither a data line nor a delimiter. 
            # It might be raw JSON-L (NDJSON) without 'data:' prefix.
            # If we have a buffer, this line breaks the SSE stream pattern, so flush first.
            if current_data_buffer:
                try:
                    valid_objects.append(json.loads("\n".join(current_data_buffer)))
                except:
                    pass
                current_data_buffer = []

            # Try parsing this line as standalone JSON
            stripped = line.strip()
            if stripped:
                try:
                    valid_objects.append(json.loads(stripped))
                except json.JSONDecodeError:
                    pass

    # Flush any remaining buffer at the end of the stream
    if current_data_buffer:
        full_data = "\n".join(current_data_buffer)
        try:
            valid_objects.append(json.loads(full_data))
        except json.JSONDecodeError:
            pass

    if valid_objects:
        # Return the last valid result, or prefer the one containing 'result' or 'error'
        for obj in reversed(valid_objects):
            if "result" in obj or "error" in obj:
                return obj
        return valid_objects[-1]

    if response.status_code == 202:
        return {}

    raise Exception(f"Could not parse server response. Raw: {text_content[:200]}...")


# --- Main Tools Class ---


class Tools:
    class Valves(BaseModel):
        MCP_SERVER_URL: str = Field(
            default="https://mcp.deepwiki.com/mcp",
            description="The MCP Server URL (Streamable HTTP Endpoint).",
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
        self.client_name = "OpenWebUI-MCP-Client-HTTP"
        self.client_version = "1.0.2"

    async def _debugger(self, action: str, **kwargs) -> Any:
        """
        Unified internal processor for Headers, Payloads, and Connection operations.
        """

        # --- 1. HEADERS GENERATION ---
        if action == "headers":
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Mcp-Protocol-Version": self.protocol_version,
            }
            if self.valves.MCP_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {self.valves.MCP_AUTH_TOKEN}"
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

        # --- 3. HTTP CONNECT (Initialize & Handshake) ---
        elif action == "connect":
            emitter = kwargs.get("emitter")
            url = self.valves.MCP_SERVER_URL

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Connecting via Streamable HTTP to {url}..."
                )

            try:
                session = requests.Session()
                base_headers = await self._debugger("headers")
                session.headers.update(base_headers)

                # STEP 1: Send 'initialize'
                init_payload = await self._debugger(
                    "payload",
                    method="initialize",
                    params={
                        "protocolVersion": self.protocol_version,
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {},
                        },
                        "clientInfo": {
                            "name": self.client_name,
                            "version": self.client_version,
                        },
                    },
                )

                response = session.post(
                    url, json=init_payload, timeout=self.user_valves.REQUEST_TIMEOUT
                )
                init_data = extract_response_data(response)

                if "Mcp-Session-Id" in response.headers:
                    session_id = response.headers["Mcp-Session-Id"]
                    session.headers["Mcp-Session-Id"] = session_id
                    if self.user_valves.DEBUG_MODE:
                        await emitter.emit_message(
                            f"DEBUG: Session ID acquired: {session_id}"
                        )

                server_info = init_data.get("result", {}).get("serverInfo", {})
                server_name = server_info.get("name", "Unknown Server")
                await emitter.emit(f"Connected to: {server_name}")

                # STEP 2: Send 'notifications/initialized'
                notify_payload = await self._debugger(
                    "payload", method="notifications/initialized"
                )

                session.post(
                    url,
                    json=notify_payload,
                    timeout=self.user_valves.REQUEST_TIMEOUT,
                )

                return session, url

            except Exception as e:
                raise Exception(f"Connection failed: {str(e)}")

        else:
            raise ValueError(f"Unknown _debugger action: {action}")

    async def deepwiki_description(
        self, __event_emitter__: Callable[[dict], Any] = None, __user__: Dict = None
    ) -> str:
        """
        refresh deepwiki descripton
        """
        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Connecting to MCP Server...")

        try:
            session, url = await self._debugger("connect", emitter=emitter)

            list_payload = await self._debugger(
                "payload", method="tools/list", request_id=2
            )

            await emitter.emit(f"Refreshing Description...")

            response = session.post(
                url,
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

    async def deepwiki(
        self,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        list all available tools for deepwiki
        """
        if __user__ and "valves" in __user__:
            self.user_valves = __user__.get("valves", self.user_valves)

        return (
            self.user_valves.TOOL_INFO_CACHE
            if self.user_valves.TOOL_INFO_CACHE != ""
            else (await self.deepwiki_description(__event_emitter__, __user__))
        )

    async def deepwiki_exec(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Execute a specific tool
        """
        if __user__ and "valves" in __user__:
            self.user_valves = __user__.get("valves", self.user_valves)

        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Calling tool: {tool_name}...")

        try:
            session, url = await self._debugger("connect", emitter=emitter)

            call_payload = await self._debugger(
                "payload",
                method="tools/call",
                params={"name": tool_name, "arguments": arguments},
                request_id=3,
            )

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Calling {tool_name} with {json.dumps(arguments)}"
                )

            response = session.post(
                url,
                json=call_payload,
                timeout=self.user_valves.REQUEST_TIMEOUT,
            )

            data = extract_response_data(response)

            if "error" in data:
                error_msg = data["error"].get("message", "Unknown Error")
                await emitter.emit(
                    status="error",
                    description=f"Tool Error: {error_msg}",
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