"""
title: MCP Client (Multi-Server Streamable HTTP)
author: OpenWebUI User
version: 0.3.0
license: MIT
description: A generic client to connect to MULTIPLE MCP Servers using the Streamable HTTP transport. Handles tool namespacing automatically.
"""

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, Optional, List

# Helper class to manage events
class EventEmitter:
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
            await self.event_emitter(
                {
                    "type": "message",
                    "data": {
                        "content": content
                    }
                }
            )

class Tools:
    class Valves(BaseModel):
        MCP_SERVER_URLS: str = Field(
            default="https://mcp.context7.com/mcp,http://localhost:8000/mcp",
            description="Comma-separated list of MCP Server URLs (e.g. 'url1,url2').",
        )
        MCP_AUTH_TOKEN: str = Field(
            default="",
            description="Optional Bearer token (applied to all servers if required).",
        )
        
    class UserValves(BaseModel):
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="Timeout in seconds for MCP requests.",
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="Enable detailed logging of JSON-RPC payloads.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()
        self.protocol_version = "2024-11-05"
        self.client_name = "OpenWebUI-MCP-Client-Multi"
        self.client_version = "1.0.0"

    def _get_headers(self, session_id: str = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream;q=0.5",
            "User-Agent": f"{self.client_name}/{self.client_version}",
            "Mcp-Protocol-Version": self.protocol_version
        }
        if self.valves.MCP_AUTH_TOKEN:
            headers["Authorization"] = f"Bearer {self.valves.MCP_AUTH_TOKEN}"
        if session_id:
            headers["Mcp-Session-Id"] = session_id
        return headers

    def _json_rpc_payload(self, method: str, params: Optional[Dict] = None, request_id: int = 1) -> Dict:
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }
        if params is not None:
            payload["params"] = params
        return payload

    def _parse_urls(self) -> List[str]:
        """Split the comma-separated string into a clean list of URLs"""
        if not self.valves.MCP_SERVER_URLS:
            return []
        return [url.strip() for url in self.valves.MCP_SERVER_URLS.split(',') if url.strip()]

    async def _handshake(self, url: str, emitter: Any) -> str:
        """
        Performs the MCP initialization handshake for a specific URL.
        """
        init_payload = self._json_rpc_payload("initialize", {
            "protocolVersion": self.protocol_version,
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {}
            },
            "clientInfo": {
                "name": self.client_name,
                "version": self.client_version
            }
        })

        if self.user_valves.DEBUG_MODE:
            await emitter.emit_message(f"DEBUG: Sending Initialize to {url}")

        try:
            handshake_timeout = max(10, self.user_valves.REQUEST_TIMEOUT // 5)
            
            response = requests.post(
                url,
                headers=self._get_headers(),
                json=init_payload,
                timeout=handshake_timeout
            )
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text}")

            session_id = response.headers.get("Mcp-Session-Id")
            data = response.json()
            
            if "error" in data:
                raise Exception(f"MCP Initialize Error: {data['error']}")

            # Send Initialized Notification
            notify_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            requests.post(
                url,
                headers=self._get_headers(session_id),
                json=notify_payload,
                timeout=5
            )
            
            return session_id

        except Exception as e:
            # We define specific behavior for handshake failure in the loop
            raise e

    async def discover_mcp_tools(
        self,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Connect to ALL configured MCP Servers and aggregate available tools.
        """
        self.user_valves = __user__.get("valves", self.user_valves)
        emitter = EventEmitter(__event_emitter__)
        
        urls = self._parse_urls()
        if not urls:
            return json.dumps({"error": "No MCP Server URLs configured."})

        await emitter.emit(f"Scanning {len(urls)} servers...")

        all_tools = []
        errors = []

        for idx, url in enumerate(urls):
            try:
                session_id = await self._handshake(url, emitter)
                
                # Request Tool List
                list_payload = self._json_rpc_payload("tools/list", {}, request_id=2)
                
                response = requests.post(
                    url,
                    headers=self._get_headers(session_id),
                    json=list_payload,
                    timeout=max(30, self.user_valves.REQUEST_TIMEOUT // 2)
                )
                
                if response.status_code == 200:
                    result = response.json()
                    tools = result.get("result", {}).get("tools", [])
                    
                    for tool in tools:
                        # NAMESPACING: Prefix tool name with server index to avoid collisions
                        # e.g. "0__weather_tool"
                        original_name = tool["name"]
                        namespaced_name = f"{idx}__{original_name}"
                        
                        all_tools.append({
                            "name": namespaced_name,
                            "description": f"[Server {idx+1}] {tool.get('description', '')}",
                            "input_schema": tool.get("inputSchema", {})
                        })
                else:
                    errors.append(f"Server {idx+1} ({url}): HTTP {response.status_code}")

            except Exception as e:
                errors.append(f"Server {idx+1} ({url}): {str(e)}")
                if self.user_valves.DEBUG_MODE:
                    await emitter.emit_message(f"DEBUG: Failed to connect to {url}: {e}")

        if not all_tools and errors:
            return json.dumps({"error": f"Discovery failed. Errors: {'; '.join(errors)}"})

        status_msg = f"Found {len(all_tools)} tools across {len(urls)} servers."
        if errors:
            status_msg += f" (Failed: {len(errors)})"
            
        await emitter.emit(status="complete", description=status_msg, done=True)
        return json.dumps(all_tools, ensure_ascii=False, indent=2)

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Execute a tool. Handles routing to the correct server based on the tool name prefix.
        """
        emitter = EventEmitter(__event_emitter__)
        self.user_valves = __user__.get("valves", self.user_valves)
        
        # Parse namespaced tool name
        try:
            server_idx_str, actual_tool_name = tool_name.split("__", 1)
            server_idx = int(server_idx_str)
            
            urls = self._parse_urls()
            if server_idx < 0 or server_idx >= len(urls):
                raise ValueError("Invalid server index")
                
            target_url = urls[server_idx]
        except ValueError:
            return json.dumps({"error": f"Invalid tool name format: {tool_name}. Expected 'index__toolname'."})

        await emitter.emit(f"Calling {actual_tool_name} on Server {server_idx+1}...")

        try:
            # Re-handshake with specific target server
            session_id = await self._handshake(target_url, emitter)

            call_payload = self._json_rpc_payload("tools/call", {
                "name": actual_tool_name,
                "arguments": arguments
            }, request_id=3)

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(f"DEBUG: Sending to {target_url}: {json.dumps(call_payload)}")

            response = requests.post(
                target_url,
                headers=self._get_headers(session_id),
                json=call_payload,
                timeout=self.user_valves.REQUEST_TIMEOUT 
            )
            
            if response.status_code != 200:
                 return json.dumps({"error": f"HTTP {response.status_code}: {response.text}"})

            data = response.json()

            if "error" in data:
                err_msg = data["error"].get("message", "Unknown error")
                await emitter.emit(status="error", description=f"Tool error: {err_msg}", done=True)
                return json.dumps({"error": data["error"]})

            content = data.get("result", {}).get("content", [])
            
            text_results = []
            for item in content:
                if item.get("type") == "text":
                    text_results.append(item.get("text"))
                elif item.get("type") == "resource":
                    text_results.append(f"[Resource: {item.get('resource').get('uri')}]")
            
            final_output = "\n".join(text_results)

            await emitter.emit(status="complete", description="Tool execution successful", done=True)
            return final_output if final_output else json.dumps(data)

        except Exception as e:
            await emitter.emit(status="error", description=f"Execution failed: {str(e)}", done=True)
            return json.dumps({"error": str(e)})