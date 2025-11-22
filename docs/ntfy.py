"""
title: Ntfy Notifier
author: stevessr
version: 0.1.0
license: MIT
description: Allows the model to send Push Notifications via ntfy.sh (or self-hosted ntfy) to your devices.
"""

import requests
import json
from pydantic import BaseModel, Field
from typing import Callable, Any, Dict, Optional

# --- Helper Classes ---


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


# --- Main Tools Class ---


class Tools:
    class Valves(BaseModel):
        NTFY_SERVER_URL: str = Field(
            default="https://ntfy.sh",
            description="Ntfy server URL (default: https://ntfy.sh, or your self-hosted URL).",
        )
        NTFY_TOPIC: str = Field(
            default="",
            description="The Ntfy topic to publish to (Required). e.g. 'my_secret_topic_123'",
        )
        NTFY_TOKEN: str = Field(
            default="",
            description="Optional Access Token (tk_...) if your Ntfy topic is protected/reserved.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def push_notification(
        self,
        message: str,
        title: str = "OpenWebUI Alert",
        priority: str = "default",
        tags: str = "",
        click_action: str = "",
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Send a push notification to the user's device via Ntfy.
        Use this tool when you need to alert the user about a completed task, a reminder, or an urgent issue.

        :param message: The main content/body of the notification.
        :param title: The title of the notification (default: OpenWebUI Alert).
        :param priority: Priority level: 'min', 'low', 'default', 'high', 'max', or 'urgent'.
        :param tags: Comma-separated list of tags or emojis (e.g., "warning,skull,white_check_mark").
        :param click_action: Optional URL to open when the user clicks the notification.
        """
        emitter = EventEmitter(__event_emitter__)

        # 1. Validate Configuration
        if not self.valves.NTFY_TOPIC:
            error_msg = "Error: NTFY_TOPIC is not configured in Valves. Please set it in the tool settings."
            await emitter.emit(
                status="error", description="Missing Configuration", done=True
            )
            return json.dumps({"error": error_msg})

        # 2. Prepare Request
        base_url = self.valves.NTFY_SERVER_URL.rstrip("/")
        topic = self.valves.NTFY_TOPIC
        target_url = f"{base_url}/{topic}"

        await emitter.emit(f"Sending notification to topic '{topic}'...")

        headers = {
            "Title": title.encode(
                "utf-8"
            ),  # Encode to handle special chars if needed in headers
            "Priority": priority,
        }

        if tags:
            headers["Tags"] = tags
        if click_action:
            headers["Click"] = click_action
        if self.valves.NTFY_TOKEN:
            headers["Authorization"] = f"Bearer {self.valves.NTFY_TOKEN}"

        # 3. Send Request
        try:
            response = requests.post(
                target_url, data=message.encode("utf-8"), headers=headers, timeout=10
            )

            if response.status_code == 200:
                result_msg = f"Notification sent successfully to topic '{topic}'."
                await emitter.emit(
                    status="complete", description="Notification Sent", done=True
                )
                return result_msg
            else:
                error_msg = f"Failed to send notification. HTTP {response.status_code}: {response.text}"
                await emitter.emit(
                    status="error", description="Failed to Send", done=True
                )
                return json.dumps({"error": error_msg})

        except Exception as e:
            await emitter.emit(
                status="error", description=f"Connection Error: {str(e)}", done=True
            )
            return json.dumps({"error": f"Ntfy Connection Failed: {str(e)}"})
