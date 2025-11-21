"""
title: Gemini Image Generation Tool
author: Claude Code
version: 0.1.0
license: MIT
description: A tool to generate images using Google's Gemini models.
"""

import requests
import json
import base64
from pydantic import BaseModel, Field
from typing import Callable, Any, Literal, Optional

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


# --- Main Tools Class ---


class Tools:
    class Valves(BaseModel):
        BASE_URL: str = Field(
            default="https://generativelanguage.googleapis.com",
            description="Base URL for Google Generative Language API.",
        )
        API_VERSION: Literal["v1beta", "v1"] = Field(
            default="v1beta", description="API version to use."
        )
        GOOGLE_API_KEY: str = Field(
            default="", description="Your Google AI API Key for Gemini."
        )
        MODEL_NAME: str = Field(
            default="gemini-2.5-flash-image",
            description="The specific Gemini model to use for image generation, e.g., 'gemini-2.5-flash-image'.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def generate_image(
        self,
        prompt: str,
        aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = "1:1",
        image_input: Optional[str] = None,
        __event_emitter__: Callable[[dict], Any] = None,
    ) -> str:
        """
        Generates an image based on a textual prompt and an optional input image.

        :param prompt: The text prompt describing the image to generate.
        :param aspect_ratio: The desired aspect ratio for the generated image.
        :param image_input: Optional. A public URL or a base64 encoded data URI of an image to include.
        """
        emitter = EventEmitter(__event_emitter__)

        if not self.valves.GOOGLE_API_KEY:
            error_msg = "Error: GOOGLE_API_KEY is not configured. Please set it in the tool settings."
            await emitter.emit(
                status="error", description="Missing Configuration", done=True
            )
            return json.dumps({"error": error_msg})

        base_url = f"{self.valves.BASE_URL}/{self.valves.API_VERSION}/model/{self.valves.MODEL_NAME}:generateContent"
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.valves.GOOGLE_API_KEY,
        }

        parts = [{"text": prompt}]
        if image_input:
            try:
                if image_input.startswith("http"):
                    # Handle URL
                    image_response = requests.get(image_input, timeout=20)
                    image_response.raise_for_status()
                    content_type = image_response.headers.get(
                        "Content-Type", "image/png"
                    )
                    image_b64 = base64.b64encode(image_response.content).decode("utf-8")
                elif image_input.startswith("data:"):
                    # Handle base64 data URI
                    header, encoded = image_input.split(",", 1)
                    content_type = header.split(";")[0].split(":")[1]
                    image_b64 = encoded
                else:
                    return json.dumps(
                        {
                            "error": "Invalid image_input format. Must be a public URL or a base64 data URI."
                        }
                    )

                parts.append(
                    {"inline_data": {"mime_type": content_type, "data": image_b64}}
                )
            except Exception as e:
                return json.dumps({"error": f"Failed to process image_input: {str(e)}"})

        # The payload for gemini-2.5-flash-image, structured in a dialogue style.
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                }
            },
        }

        await emitter.emit(f"Generating image for prompt: '{prompt}'...")

        try:
            response = requests.post(
                f"{self.valves.BASE_URL}/{self.valves.API_VERSION}/model/{self.valves.MODEL_NAME}:generateContent",
                headers=headers,
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            image_data = response.json()

            if (
                "candidates" in image_data
                and "content" in image_data["candidates"][0]
                and "parts" in image_data["candidates"][0]["content"]
            ):
                for part in image_data["candidates"][0]["content"]["parts"]:
                    if "inlineData" in part:
                        image_base64 = part["inlineData"]["data"]
                        await emitter.emit(
                            status="complete", description="Image Generated", done=True
                        )
                        return f"SUCCESS: Image generated. Raw base64 data follows:\\n\\n{image_base64}"

            # If no image data is found
            error_msg = "Failed to generate image. No inlineData found in the response."
            await emitter.emit(status="error", description=error_msg, done=True)
            return json.dumps({"error": error_msg, "details": image_data})

        except requests.exceptions.HTTPError as e:
            error_details = e.response.text
            error_msg = f"HTTP Error {e.response.status_code}: {error_details}"
            await emitter.emit(
                status="error",
                description=f"HTTP Error: {e.response.status_code}",
                done=True,
            )
            return json.dumps({"error": error_msg})
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            await emitter.emit(
                status="error", description=f"Connection Error: {str(e)}", done=True
            )
            return json.dumps({"error": error_msg})
