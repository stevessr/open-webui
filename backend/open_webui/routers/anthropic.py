import asyncio
import hashlib
import json
import logging
from typing import Optional

import aiohttp
import requests
from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.responses import (
    FileResponse,
    StreamingResponse,
    JSONResponse,
    PlainTextResponse,
)
from pydantic import BaseModel

from open_webui.models.models import Models
from open_webui.config import (
    CACHE_DIR,
)
from aiocache import cached
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
    convert_openai_tool_choice_to_anthropic,
    convert_openai_tools_to_anthropic,
)
from open_webui.utils.misc import (
    stream_chunks_handler,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access
from starlette.background import BackgroundTask


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OPENAI"])


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
                    **({"x-api-key": f"{key}"} if key else {}),
                    "anthropic-version": "2023-06-01",
                    **(
                        {
                            "X-OpenWebUI-User-Name": user.name,
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
        # Handle connection error here
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
        **({"x-api-key": f"{key}"} if key else {}),
    }

    if config.get("headers") and isinstance(config.get("headers"), dict):
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
    if not request.app.state.config.ENABLE_ANTHROPIC_API:
        return {"data": []}

    # Check if API KEYS length is same than API URLS length
    num_urls = len(request.app.state.config.ANTHROPIC_API_BASE_URLS)
    num_keys = len(request.app.state.config.ANTHROPIC_API_KEYS)

    if num_keys != num_urls:
        # if there are more keys than urls, remove the extra keys
        if num_keys > num_urls:
            new_keys = request.app.state.config.ANTHROPIC_API_KEYS[:num_urls]
            request.app.state.config.ANTHROPIC_API_KEYS = new_keys
        # if there are more urls than keys, add empty keys
        else:
            request.app.state.config.ANTHROPIC_API_KEYS += [""] * (num_urls - num_keys)

    request_tasks = []
    for idx, url in enumerate(request.app.state.config.ANTHROPIC_API_BASE_URLS):
        if (str(idx) not in request.app.state.config.ANTHROPIC_API_CONFIGS) and (
            url not in request.app.state.config.ANTHROPIC_API_CONFIGS  # Legacy support
        ):
            # Try to fetch models from Anthropic API
            request_tasks.append(
                send_get_request(
                    f"{url}/models",
                    request.app.state.config.ANTHROPIC_API_KEYS[idx],
                    user=user,
                )
            )
        else:
            api_config = request.app.state.config.ANTHROPIC_API_CONFIGS.get(
                str(idx),
                request.app.state.config.ANTHROPIC_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            enable = api_config.get("enable", True)
            model_ids = api_config.get("model_ids", [])

            if enable:
                if len(model_ids) == 0:
                    # Try to fetch models from Anthropic API endpoint
                    request_tasks.append(
                        send_get_request(
                            f"{url}/models",
                            request.app.state.config.ANTHROPIC_API_KEYS[idx],
                            user=user,
                        )
                    )
                else:
                    # Use model_ids from config
                    model_list = {
                        "object": "list",
                        "data": [
                            {
                                "id": model_id,
                                "name": model_id,
                                "owned_by": "anthropic",
                                "anthropic": {"id": model_id},
                                "urlIdx": idx,
                            }
                            for model_id in model_ids
                        ],
                    }

                    request_tasks.append(
                        asyncio.ensure_future(asyncio.sleep(0, model_list))
                    )
            else:
                request_tasks.append(asyncio.ensure_future(asyncio.sleep(0, None)))

    responses = await asyncio.gather(*request_tasks)

    def extract_data(response):
        if response and "data" in response:
            return response["data"]
        if isinstance(response, list):
            return response
        return None

    def get_merged_models(model_lists):
        models = {}
        for idx, model_list in enumerate(model_lists):
            if model_list is not None and "error" not in model_list:
                for model in model_list:
                    model_id = model.get("id") or model.get("name")
                    if model_id and model_id not in models:
                        # Anthropic API returns 'display_name' instead of 'name'
                        model_name = (
                            model.get("name") or model.get("display_name") or model_id
                        )

                        models[model_id] = {
                            **model,
                            "id": model_id,
                            "name": model_name,
                            "owned_by": "anthropic",
                            "anthropic": {
                                **model,
                                "original_id": model_id,  # Store original ID
                            },
                            "connection_type": model.get("connection_type", "external"),
                            "urlIdx": idx,
                        }
        return models

    models = get_merged_models(map(extract_data, responses))
    request.app.state.ANTHROPIC_MODELS = models

    if user.role == "user" and not BYPASS_MODEL_ACCESS_CONTROL:
        # Filter models based on user access control
        filtered_models = []
        for model in models.values():
            model_info = Models.get_model_by_id(model["id"])
            if model_info:
                if user.id == model_info.user_id or has_access(
                    user.id, type="read", access_control=model_info.access_control
                ):
                    filtered_models.append(model)
            else:
                # If no model info, assume access is allowed
                filtered_models.append(model)

        return {"data": filtered_models}

    return {"data": list(models.values())}


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

    # For now we just use the first available config/key since we don't dynamic model loading
    idx = 0

    # Get the API config for the model
    api_config = request.app.state.config.ANTHROPIC_API_CONFIGS.get(
        str(idx),
        request.app.state.config.ANTHROPIC_API_CONFIGS.get(
            request.app.state.config.ANTHROPIC_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.ANTHROPIC_API_BASE_URLS[idx]
    key = request.app.state.config.ANTHROPIC_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, metadata, user=user
    )

    # Transform OpenAI format to Anthropic format
    # Extract system message if present
    messages = payload.get("messages", [])
    system_message = None
    new_messages = []

    for msg in messages:
        if msg["role"] == "system":
            system_message = msg["content"]
        else:
            new_messages.append(msg)

    anthropic_payload = {
        "model": payload.get("model"),
        "messages": new_messages,
        "max_tokens": payload.get("max_tokens", 4096),
        "stream": payload.get("stream", False),
    }

    if system_message:
        anthropic_payload["system"] = system_message

    if "temperature" in payload:
        anthropic_payload["temperature"] = payload["temperature"]

    if "top_p" in payload:
        anthropic_payload["top_p"] = payload["top_p"]

    # Add Anthropic-specific parameters
    if "thinking_enabled" in payload and payload["thinking_enabled"]:
        anthropic_payload["thinking"] = {
            "type": "enabled",
            "budget_tokens": payload.get("thinking_budget", 1024),
        }

    if "tool_choice" in payload:
        tool_choice = convert_openai_tool_choice_to_anthropic(payload["tool_choice"])
        if tool_choice:
            anthropic_payload["tool_choice"] = tool_choice

    if "tools" in payload:
        anthropic_payload["tools"] = convert_openai_tools_to_anthropic(payload["tools"])

    request_url = f"{url}/messages"
    payload_json = json.dumps(anthropic_payload)

    r = None
    session = None
    streaming = False
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

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                # We need a handler to convert Anthropic SSE to OpenAI SSE format
                # For now let's assume simple streaming
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            try:
                response = await r.json()

                # Convert Anthropic response to OpenAI format
                if "content" in response:
                    content = ""
                    thinking_content = ""

                    # Extract regular content and thinking content
                    for content_block in response["content"]:
                        if content_block["type"] == "text":
                            content += content_block["text"]
                        elif content_block["type"] == "thinking":
                            thinking_content += content_block["thinking"]

                    openai_response = {
                        "id": response["id"],
                        "object": "chat.completion",
                        "created": int(asyncio.get_event_loop().time()),
                        "model": response["model"],
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": content},
                                "finish_reason": response["stop_reason"],
                            }
                        ],
                        "usage": {
                            "prompt_tokens": response["usage"]["input_tokens"],
                            "completion_tokens": response["usage"]["output_tokens"],
                            "total_tokens": response["usage"]["input_tokens"]
                            + response["usage"]["output_tokens"],
                        },
                    }

                    # Add thinking content if present
                    if thinking_content:
                        openai_response["choices"][0]["message"]["thinking"] = (
                            thinking_content
                        )

                    response = openai_response

            except Exception as e:
                log.error(e)
                response = await r.text()

            if r.status >= 400:
                if isinstance(response, (dict, list)):
                    return JSONResponse(status_code=r.status, content=response)
                else:
                    return PlainTextResponse(status_code=r.status, content=response)

            return response
    except Exception as e:
        log.exception(e)

        raise HTTPException(
            status_code=r.status if r else 500,
            detail="Open WebUI: Server Connection Error",
        )
    finally:
        if not streaming:
            await cleanup_response(r, session)


@router.post("/messages")
async def create_message(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    """Direct Anthropic-style messages endpoint"""
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    # For now we just use the first available config/key
    idx = 0

    # Get the API config for the model
    api_config = request.app.state.config.ANTHROPIC_API_CONFIGS.get(
        str(idx),
        request.app.state.config.ANTHROPIC_API_CONFIGS.get(
            request.app.state.config.ANTHROPIC_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.ANTHROPIC_API_BASE_URLS[idx]
    key = request.app.state.config.ANTHROPIC_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, user=user
    )

    # Use the form_data directly as it's already in Anthropic format
    anthropic_payload = form_data

    # Construct the direct Anthropic API URL
    request_url = f"{url}/messages"
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

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            # Return the raw stream directly from Anthropic
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            try:
                response = await r.json()

                if r.status >= 400:
                    if isinstance(response, (dict, list)):
                        return JSONResponse(status_code=r.status, content=response)
                    else:
                        return PlainTextResponse(status_code=r.status, content=response)

                return response

            except Exception as e:
                log.error(e)
                response = await r.text()
                return PlainTextResponse(status_code=r.status, content=response)

    except Exception as e:
        log.exception(e)
        if r and not r.closed:
            await cleanup_response(r, session)
        raise HTTPException(
            status_code=r.status if r else 500,
            detail="Open WebUI: Server Connection Error",
        )



class ConnectionVerificationForm(BaseModel):
    url: str
    key: str

    config: Optional[dict] = None


@router.post("/verify")
async def verify_connection(
    request: Request,
    form_data: ConnectionVerificationForm,
    user=Depends(get_admin_user),
):
    url = form_data.url
    key = form_data.key
    api_config = form_data.config or {}

    # Verify by trying to create a message with a simple prompt
    # Anthropic doesn't have a simple 'validate key' endpoint that doesn't charge money/tokens
    # But we can try a very small request

    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "x-api-key": key,
    }

    async with aiohttp.ClientSession(
        trust_env=True,
        timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST),
    ) as session:
        try:
            # We use a dummy model list check or something minimal if possible
            # Since Anthropic doesn't have /models endpoint, we might need to send a dummy message
            # However, to avoid costs, maybe just check if we can connect?
            # For now let's trust if we can reach the API or try a cheap model

            # Actually, let's try a very simple message to haiku which is cheap
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "Hi"}],
            }

            async with session.post(
                f"{url}/messages",
                headers=headers,
                json=payload,
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as r:
                if r.status != 200:
                    detail = f"HTTP Error: {r.status}"
                    res = await r.json()
                    if "error" in res:
                        detail = f"External Error: {res['error']['message']}"
                    raise Exception(detail)

                return {"status": True}

        except aiohttp.ClientError as e:
            log.exception(f"Client error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Open WebUI: Server Connection Error"
            )
        except Exception as e:
            log.exception(f"Unexpected error: {e}")
            error_detail = f"Unexpected error: {str(e)}"
            raise HTTPException(status_code=500, detail=error_detail)
