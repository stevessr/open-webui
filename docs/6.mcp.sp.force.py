"""
title: MCP Client (Streamable HTTP) specialization for bright_data
author: stevessr
version: 0.2.5
license: MIT
description: MCP Client specialized for bright_data using Streamable HTTP transport.
"""

DEFAULT_URL = "https://mcp.brightdata.com/mcp"

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict


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
            await self.event_emitter({"type": "message", "data": {"content": content}})


class Tools:
    class Valves(BaseModel):
        MCP_SERVER_URL: str = Field(
            default=DEFAULT_URL,
            description="The endpoint URL of bright_data (Streamable HTTP supported).",
        )
        MCP_AUTH_TOKEN: str = Field(
            default="",
            description="Optional Bearer token if bright_data requires authentication.",
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

    async def _debugger(self, action: str, **kwargs) -> Any:
        """
        Unified internal manager for MCP operations.
        :param action: 'headers', 'payload', or 'handshake'
        :param kwargs: Arguments specific to the action
        """

        # --- Action: Generate Headers ---
        if action == "headers":
            session_id = kwargs.get("session_id")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream;q=0.5",
                "User-Agent": f"{self.client_name}/{self.client_version}",
                "Mcp-Protocol-Version": self.protocol_version,
            }
            if self.valves.MCP_AUTH_TOKEN:
                headers["Authorization"] = f"Bearer {self.valves.MCP_AUTH_TOKEN}"
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            return headers

        # --- Action: Generate JSON-RPC Payload ---
        elif action == "payload":
            payload = {
                "jsonrpc": "2.0",
                "method": kwargs.get("method"),
                "id": kwargs.get("request_id", 1),
            }
            params = kwargs.get("params")
            if params is not None:
                payload["params"] = params
            return payload

        # --- Action: Perform Handshake ---
        elif action == "handshake":
            emitter = kwargs.get("emitter")
            if emitter is None:
                emitter = EventEmitter(None)

            # Construct Init Payload recursively
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
                },
            )

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Sending Initialize: {json.dumps(init_payload)}"
                )

            try:
                # 1. Send Initialize
                handshake_timeout = max(30, self.user_valves.REQUEST_TIMEOUT // 5)

                # Get headers recursively
                req_headers = await self._debugger("headers")

                response = requests.post(
                    self.valves.MCP_SERVER_URL,
                    headers=req_headers,
                    json=init_payload,
                    timeout=handshake_timeout,
                )

                if response.status_code != 200:
                    raise Exception(
                        f"HTTP {response.status_code} Error: {response.text}"
                    )

                # Streamable HTTP servers return session ID in headers
                session_id = response.headers.get("Mcp-Session-Id")

                data = response.json()
                if "error" in data:
                    raise Exception(f"MCP Initialize Error: {data['error']}")

                server_info = data.get("result", {}).get("serverInfo", {})
                server_name = server_info.get("name", "Unknown Server")
                await emitter.emit(
                    f"Connected to: {server_name} (Session: {session_id})"
                )

                # 2. Send Initialized Notification (Required by protocol)
                notify_payload = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized",
                }

                # Get headers with session ID recursively
                notify_headers = await self._debugger("headers", session_id=session_id)

                requests.post(
                    self.valves.MCP_SERVER_URL + f"?token={self.valves.MCP_AUTH_TOKEN}",
                    headers=notify_headers,
                    json=notify_payload,
                    timeout=10,
                )

                return session_id

            except Exception as e:
                await emitter.emit(
                    status="error", description=f"Handshake failed: {str(e)}", done=True
                )
                raise e

        else:
            raise ValueError(f"Unknown internal action: {action}")

    async def bright_data_tools(
        self,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        list all available tools for bright_data via MCP.
        ALWAYS call this first to see what tools are supported by the server.
        :return: A JSON string listing available tools and their schemas.
        """
        if not self.valves.MCP_AUTH_TOKEN:
            return json.dumps({"error": "MCP_AUTH_TOKEN is required to list tools."})
        self.user_valves = __user__.get("valves", self.user_valves)
        emitter = EventEmitter(__event_emitter__)
        await emitter.emit(f"Connecting to {self.valves.MCP_SERVER_URL}...")

        try:
            # Execute Handshake via Manager
            session_id = await self._debugger("handshake", emitter=emitter)

            # 3. Request Tool List
            list_payload = await self._debugger(
                "payload", method="tools/list", params={}, request_id=2
            )
            headers = await self._debugger("headers", session_id=session_id)

            discovery_timeout = max(60, self.user_valves.REQUEST_TIMEOUT // 2)

            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=headers,
                json=list_payload,
                timeout=discovery_timeout,
            )

            if response.status_code != 200:
                return json.dumps(
                    {"error": f"HTTP {response.status_code}: {response.text}"}
                )

            result = response.json()

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
            return json.dumps(tool_summaries, ensure_ascii=False, indent=2)

        except Exception as e:
            return json.dumps({"error": f"Failed to discover tools: {str(e)}"})

    async def bright_data_exec(
        self,
        tool_name: str,
        arguments: dict,
        __event_emitter__: Callable[[dict], Any] = None,
        __user__: Dict = None,
    ) -> str:
        """
        Execute a specific tool for bright_data via MCP.
        :params tool_name: The name of the tool to call (get this from discover_mcp_tools).
        :params arguments: The dictionary of arguments required by the tool schema.
        :return: The result of the tool execution.
        """
        if not self.valves.MCP_AUTH_TOKEN:
            return json.dumps({"error": "MCP_AUTH_TOKEN is required to list tools."})
        emitter = EventEmitter(__event_emitter__)
        self.user_valves = __user__.get("valves", self.user_valves)
        await emitter.emit(f"Calling tool: {tool_name}...")

        try:
            # Execute Handshake via Manager
            session_id = await self._debugger("handshake", emitter=emitter)

            call_payload = await self._debugger(
                "payload",
                method="tools/call",
                params={"name": tool_name, "arguments": arguments},
                request_id=3,
            )

            if self.user_valves.DEBUG_MODE:
                await emitter.emit_message(
                    f"DEBUG: Call Payload: {json.dumps(call_payload)}"
                )

            headers = await self._debugger("headers", session_id=session_id)

            response = requests.post(
                self.valves.MCP_SERVER_URL,
                headers=headers,
                json=call_payload,
                timeout=self.user_valves.REQUEST_TIMEOUT,
            )

            if response.status_code != 200:
                return json.dumps(
                    {"error": f"HTTP {response.status_code}: {response.text}"}
                )

            data = response.json()

            if "error" in data:
                err_msg = data["error"].get("message", "Unknown error")
                await emitter.emit(
                    status="error", description=f"Tool error: {err_msg}", done=True
                )
                return json.dumps({"error": data["error"]})

            content = data.get("result", {}).get("content", [])

            text_results = []
            for item in content:
                if item.get("type") == "text":
                    text_results.append(item.get("text"))
                elif item.get("type") == "resource":
                    text_results.append(
                        f"[Resource: {item.get('resource').get('uri')}]"
                    )

            final_output = "\n".join(text_results)

            await emitter.emit(
                status="complete", description="Tool execution successful", done=True
            )
            return final_output if final_output else json.dumps(data)

        except Exception as e:
            await emitter.emit(
                status="error", description=f"Execution failed: {str(e)}", done=True
            )
            return json.dumps({"error": str(e)})
