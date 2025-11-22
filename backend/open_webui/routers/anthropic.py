import asyncio
import hashlib
import json
import logging
from typing import Optional

import aiohttp
from aiocache import cached
import requests
from urllib.parse import quote

from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from open_webui.models.models import Models
from open_webui.config import CACHE_DIR
from open_webui.env import (
    MODELS_CACHE_TTL,
    AIOHTTP_CLIENT_SESSION_SSL,
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.models.users import UserModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS

from open_webui.utils.payload import (
    apply_model_params_to_body_openai,
    apply_system_prompt_to_body,
)
from open_webui.utils.misc import (
    stream_chunks_handler,
)

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS.get("MODELS", "INFO"))


##########################################
#
# Utility functions
#
##########################################


async def send_get_request(url, key=None, user: UserModel = None):
    timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    try:
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(
                url,
                headers={
                    "anthropic-version": "2023-06-01",
                    **({"x-api-key": key} if key else {}),
                    **(
                        {
                            "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                            "X-OpenWebUI-User-Id": user.id,
                            "X-OpenWebUI-User-Email": user.email,
                            "X-OpenWebUI-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS and user
                        else {}
                    ),
                },
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as response:
                return await response.json()
    except Exception as e:
        log.error(f"Connection error: {e}")
        return None


async def cleanup_response(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
):
    if response:
        response.close()
    if session:
        await session.close()


async def get_headers_and_cookies(
    request: Request,
    url,
    key=None,
    config=None,
    metadata: Optional[dict] = None,
    user: UserModel = None,
):
    cookies = {}
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        **(
            {
                "X-OpenWebUI-User-Name": quote(user.name, safe=" "),
                "X-OpenWebUI-User-Id": user.id,
                "X-OpenWebUI-User-Email": user.email,
                "X-OpenWebUI-User-Role": user.role,
                **(
                    {"X-OpenWebUI-Chat-Id": metadata.get("chat_id")}
                    if metadata and metadata.get("chat_id")
                    else {}
                ),
            }
            if ENABLE_FORWARD_USER_INFO_HEADERS
            else {}
        ),
    }

    if key:
        headers["x-api-key"] = key

    if config and config.get("headers") and isinstance(config.get("headers"), dict):
        headers = {**headers, **config.get("headers")}

    return headers, cookies


##########################################
#
# API routes
#
##########################################

router = APIRouter()


@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_ANTHROPIC_API": request.app.state.config.ENABLE_ANTHROPIC_API,
        "ANTHROPIC_API_BASE_URLS": request.app.state.config.ANTHROPIC_API_BASE_URLS,
        "ANTHROPIC_API_KEYS": request.app.state.config.ANTHROPIC_API_KEYS,
        "ANTHROPIC_API_CONFIGS": request.app.state.config.ANTHROPIC_API_CONFIGS,
    }


class AnthropicConfigForm(BaseModel):
    ENABLE_ANTHROPIC_API: Optional[bool] = None
    ANTHROPIC_API_BASE_URLS: list[str]
    ANTHROPIC_API_KEYS: list[str]
    ANTHROPIC_API_CONFIGS: dict


@router.post("/config/update")
async def update_config(
    request: Request, form_data: AnthropicConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_ANTHROPIC_API = form_data.ENABLE_ANTHROPIC_API
    request.app.state.config.ANTHROPIC_API_BASE_URLS = form_data.ANTHROPIC_API_BASE_URLS
    request.app.state.config.ANTHROPIC_API_KEYS = form_data.ANTHROPIC_API_KEYS

    # Check if API KEYS length is same than API URLS length
    if len(request.app.state.config.ANTHROPIC_API_KEYS) != len(
        request.app.state.config.ANTHROPIC_API_BASE_URLS
    ):
        if len(request.app.state.config.ANTHROPIC_API_KEYS) > len(
            request.app.state.config.ANTHROPIC_API_BASE_URLS
        ):
            request.app.state.config.ANTHROPIC_API_KEYS = (
                request.app.state.config.ANTHROPIC_API_KEYS[
                    : len(request.app.state.config.ANTHROPIC_API_BASE_URLS)
                ]
            )
        else:
            request.app.state.config.ANTHROPIC_API_KEYS += [""] * (
                len(request.app.state.config.ANTHROPIC_API_BASE_URLS)
                - len(request.app.state.config.ANTHROPIC_API_KEYS)
            )

    request.app.state.config.ANTHROPIC_API_CONFIGS = form_data.ANTHROPIC_API_CONFIGS

    # Remove the API configs that are not in the API URLS
    keys = list(map(str, range(len(request.app.state.config.ANTHROPIC_API_BASE_URLS))))
    request.app.state.config.ANTHROPIC_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.ANTHROPIC_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_ANTHROPIC_API": request.app.state.config.ENABLE_ANTHROPIC_API,
        "ANTHROPIC_API_BASE_URLS": request.app.state.config.ANTHROPIC_API_BASE_URLS,
        "ANTHROPIC_API_KEYS": request.app.state.config.ANTHROPIC_API_KEYS,
        "ANTHROPIC_API_CONFIGS": request.app.state.config.ANTHROPIC_API_CONFIGS,
    }


@router.get("/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    """
    Return a static list of Anthropic models
    Anthropic doesn't provide a models endpoint, so we return known models
    """
    if not request.app.state.config.ENABLE_ANTHROPIC_API:
        return {"data": []}

    # Static list of Anthropic Claude models
    models = [
        {
            "id": "claude-3-5-sonnet-20241022",
            "name": "Claude 3.5 Sonnet (New)",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
        {
            "id": "claude-3-5-sonnet-20240620",
            "name": "Claude 3.5 Sonnet",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
        {
            "id": "claude-3-5-haiku-20241022",
            "name": "Claude 3.5 Haiku",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
        {
            "id": "claude-3-opus-20240229",
            "name": "Claude 3 Opus",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
        {
            "id": "claude-3-sonnet-20240229",
            "name": "Claude 3 Sonnet",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
        {
            "id": "claude-3-haiku-20240307",
            "name": "Claude 3 Haiku",
            "object": "model",
            "created": 0,
            "owned_by": "anthropic",
        },
    ]

    # Apply prefix_id if configured
    for idx, url in enumerate(request.app.state.config.ANTHROPIC_API_BASE_URLS):
        api_config = request.app.state.config.ANTHROPIC_API_CONFIGS.get(
            str(idx),
            request.app.state.config.ANTHROPIC_API_CONFIGS.get(url, {}),
        )
        prefix_id = api_config.get("prefix_id", None)
        model_ids = api_config.get("model_ids", [])

        if prefix_id or len(model_ids) > 0:
            filtered_models = []
            for model in models:
                model_id = model["id"]
                if len(model_ids) == 0 or model_id in model_ids:
                    if prefix_id:
                        model = model.copy()
                        model["id"] = f"{prefix_id}.{model_id}"
                    filtered_models.append(model)
            models = filtered_models
            break

    return {"data": models}


def convert_openai_to_anthropic_payload(openai_payload):
    """Convert OpenAI-style payload to Anthropic API format"""
    anthropic_payload = {
        "model": openai_payload.get("model", "claude-3-5-sonnet-20241022"),
        "messages": [],
        "max_tokens": openai_payload.get("max_tokens", 4096),
    }

    # Extract system message and convert messages
    system_messages = []
    for msg in openai_payload.get("messages", []):
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "system":
            system_messages.append(content)
        elif role in ["user", "assistant"]:
            anthropic_payload["messages"].append({
                "role": role,
                "content": content
            })

    # Set system message if present
    if system_messages:
        anthropic_payload["system"] = "\n\n".join(system_messages)

    # Map generation parameters
    if "temperature" in openai_payload:
        anthropic_payload["temperature"] = openai_payload["temperature"]
    
    if "top_p" in openai_payload:
        anthropic_payload["top_p"] = openai_payload["top_p"]
    
    if "stop" in openai_payload:
        stop_sequences = openai_payload["stop"]
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]
        anthropic_payload["stop_sequences"] = stop_sequences

    # Anthropic-specific parameters
    if "top_k" in openai_payload:
        anthropic_payload["top_k"] = openai_payload["top_k"]

    # Streaming
    if "stream" in openai_payload:
        anthropic_payload["stream"] = openai_payload["stream"]

    return anthropic_payload


@router.post("/chat/completions")
async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    idx = 0
    payload = {**form_data}
    metadata = payload.pop("metadata", None)

    model_id = form_data.get("model")
    model_info = Models.get_model_by_id(model_id)

    # Check model info and override the payload
    if model_info:
        if model_info.base_model_id:
            payload["model"] = model_info.base_model_id
            model_id = model_info.base_model_id

        params = model_info.params.model_dump()

        if params:
            system = params.pop("system", None)
            payload = apply_model_params_to_body_openai(params, payload)
            payload = apply_system_prompt_to_body(system, payload, metadata, user)

        # Check if user has access to the model
        if not bypass_filter and user.role == "user":
            if not (
                user.id == model_info.user_id
                or has_access(
                    user.id, type="read", access_control=model_info.access_control
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Model not found",
                )
    elif not bypass_filter:
        if user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Model not found",
            )

    # Use first configured URL
    if len(request.app.state.config.ANTHROPIC_API_BASE_URLS) == 0:
        raise HTTPException(
            status_code=404,
            detail="No Anthropic API URLs configured",
        )

    url = request.app.state.config.ANTHROPIC_API_BASE_URLS[idx]
    key = request.app.state.config.ANTHROPIC_API_KEYS[idx]

    # Get the API config for the model
    api_config = request.app.state.config.ANTHROPIC_API_CONFIGS.get(
        str(idx),
        request.app.state.config.ANTHROPIC_API_CONFIGS.get(url, {}),
    )

    prefix_id = api_config.get("prefix_id", None)
    if prefix_id:
        payload["model"] = payload["model"].replace(f"{prefix_id}.", "")

    # Convert OpenAI format to Anthropic format
    anthropic_payload = convert_openai_to_anthropic_payload(payload)
    
    # Determine if streaming
    is_streaming = payload.get("stream", False)
    
    # Build request URL
    request_url = f"{url}/v1/messages"

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, metadata, user=user
    )

    payload_json = json.dumps(anthropic_payload)

    r = None
    session = None
    response = None

    try:
        session = aiohttp.ClientSession(
            trust_env=True, timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
        )

        r = await session.request(
            method="POST",
            url=request_url,
            data=payload_json,
            headers=headers,
            cookies=cookies,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )

        r.raise_for_status()

        if is_streaming:
            return StreamingResponse(
                stream_chunks_handler(r.content),
                media_type="text/event-stream",
                background=BackgroundTask(cleanup_response, response=r, session=session),
            )
        else:
            response_data = await r.json()
            
            # Convert Anthropic response to OpenAI format
            openai_response = {
                "id": response_data.get("id", f"chatcmpl-{hashlib.sha256(json.dumps(response_data).encode()).hexdigest()[:8]}"),
                "object": "chat.completion",
                "created": 0,
                "model": model_id,
                "choices": [],
                "usage": response_data.get("usage", {}),
            }

            if "content" in response_data and len(response_data["content"]) > 0:
                content_text = ""
                for content_block in response_data["content"]:
                    if content_block.get("type") == "text":
                        content_text += content_block.get("text", "")

                openai_response["choices"].append({
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content_text,
                    },
                    "finish_reason": response_data.get("stop_reason", "stop"),
                })

            await cleanup_response(r, session)
            return JSONResponse(content=openai_response)

    except Exception as e:
        log.exception(e)
        error_detail = str(e)

        if r is not None:
            try:
                res = await r.json()
                error_detail = res.get("error", {}).get("message", str(e))
            except Exception:
                try:
                    error_detail = await r.text()
                except Exception:
                    pass

        await cleanup_response(r, session)

        raise HTTPException(
            status_code=getattr(r, "status", 500) if r else 500,
            detail=error_detail,
        )


@router.get("/models/list")
async def get_models_list(request: Request, user=Depends(get_verified_user)):
    """Alias for /models endpoint"""
    return await get_models(request, user)
