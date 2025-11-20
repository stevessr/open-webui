"""
title: MCP Client (Streamable HTTP)
author: OpenWebUI User
version: 0.2.4
license: MIT
description: A generic client to connect to any MCP Server using the Streamable HTTP transport. Includes configurable timeouts and strict header compliance.
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
        MCP_SERVER_URL: str = Field(
            default="https://mcp.context7.com/mcp",
            description="The endpoint URL of the MCP Server (Streamable HTTP supported).",
        )
        MCP_AUTH_TOKEN: str = Field(
            default="",
            description="Optional Bearer token if the MCP server requires authentication.",
        )
        
    
    class UserValves(BaseModel):
        REQUEST_TIMEOUT: int = Field(
            default=300,
            description="Timeout in seconds for MCP requests (default: 300s). Increase for long-running tools.",
        )
        DEBUG_MODE: bool = Field(
            default=False,
            description="Enable detailed logging of JSON-RPC payloads to the UI.",
        )

    def __init__(self):
        self.valves = self.Valves()
        self.user_valves = self.UserValves()
        # MCP Protocol Version compatibility
        self.protocol_version = "2024-11-05"
        self.client_name = "OpenWebUI-MCP-Client"
        self.client_version = "1.0.0"

    def _get_headers(self, session_id: str = None) -> Dict[str, str]:
        # Fix for 406 Error: Server requires explicit acceptance of both formats
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

    async def _handshake(self, emitter: Any) -> str:
        """
        Performs the MCP initialization handshake.
        Returns session_id if successful.
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
            await emitter.emit_message(f"DEBUG: Sending Initialize: {json.dumps(init_payload)}")

        try:
            # 1. Send Initialize
            # Handshake usually needs less time, but we use a safe fraction of the total timeout or at least 30s
            handshake_timeout = max(30, self.user_valves.REQUEST_TIMEOUT // 5)
            
            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=self._get_headers(),
                json=init_payload,
                timeout=handshake_timeout
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise Exception(f"HTTP {response.status_code} Error: {error_text}")

            # Streamable HTTP servers return session ID in headers
            session_id = response.headers.get("Mcp-Session-Id")
            
            data = response.json()
            if "error" in data:
                raise Exception(f"MCP Initialize Error: {data['error']}")

            server_info = data.get("result", {}).get("serverInfo", {})
            server_name = server_info.get("name", "Unknown Server")
            await emitter.emit(f"Connected to: {server_name} (Session: {session_id})")

            # 2. Send Initialized Notification (Required by protocol)
            notify_payload = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            requests.post(
                self.valves.MCP_SERVER_URL,
                headers=self._get_headers(session_id),
                json=notify_payload,
                timeout=10
            )
            
            return session_id

        except Exception as e:
            await emitter.emit(status="error", description=f"Handshake failed: {str(e)}", done=True)
            raise e

    async def discover_mcp_tools(
        self,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Connect to the MCP Server and list all available tools. 
        ALWAYS call this first to see what tools are supported by the server.
        :return: A JSON string listing available tools and their schemas.
        """
        self.user_valves = __user__.get("valves", self.user_valves)
        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Connecting to {self.valves.MCP_SERVER_URL}...")

        try:
            session_id = await self._handshake(emitter)
            
            # 3. Request Tool List
            list_payload = self._json_rpc_payload("tools/list", {}, request_id=2)
            
            # Discovery usually quick, but some servers generate schema dynamically
            discovery_timeout = max(60, self.user_valves.REQUEST_TIMEOUT // 2)

            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=self._get_headers(session_id),
                json=list_payload,
                timeout=discovery_timeout
            )
            
            if response.status_code != 200:
                 return json.dumps({"error": f"HTTP {response.status_code}: {response.text}"})

            result = response.json()

            if "error" in result:
                return json.dumps({"error": result["error"]})

            tools = result.get("result", {}).get("tools", [])
            
            tool_summaries = []
            for tool in tools:
                tool_summaries.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("inputSchema", {})
                })

            await emitter.emit(status="complete", description=f"Found {len(tools)} tools", done=True)
            return json.dumps(tool_summaries, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to discover tools: {str(e)}"})

    async def call_mcp_tool(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Execute a specific tool on the remote MCP Server.
        :params tool_name: The name of the tool to call (get this from discover_mcp_tools).
        :params arguments: The dictionary of arguments required by the tool schema.
        :return: The result of the tool execution.
        """
        emitter = EventEmitter(__event_emitter__)
        self.user_valves = __user__.get("valves", self.user_valves)
        await emitter.emit(f"Calling tool: {tool_name}...")

        try:
            # Re-handshake for robustness
            session_id = await self._handshake(emitter)

            call_payload = self._json_rpc_payload("tools/call", {
                "name": tool_name,
                "arguments": arguments
            }, request_id=3)

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(f"DEBUG: Call Payload: {json.dumps(call_payload)}")

            response = requests.post(
                self.valves.MCP_SERVER_URL,
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