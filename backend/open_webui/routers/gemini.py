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
                    **({"x-goog-api-key": key} if key else {}),
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
        headers["x-goog-api-key"] = key

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
        "ENABLE_GEMINI_API": request.app.state.config.ENABLE_GEMINI_API,
        "GEMINI_API_BASE_URLS": request.app.state.config.GEMINI_API_BASE_URLS,
        "GEMINI_API_KEYS": request.app.state.config.GEMINI_API_KEYS,
        "GEMINI_API_CONFIGS": request.app.state.config.GEMINI_API_CONFIGS,
    }


class GeminiConfigForm(BaseModel):
    ENABLE_GEMINI_API: Optional[bool] = None
    GEMINI_API_BASE_URLS: list[str]
    GEMINI_API_KEYS: list[str]
    GEMINI_API_CONFIGS: dict


@router.post("/config/update")
async def update_config(
    request: Request, form_data: GeminiConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_GEMINI_API = form_data.ENABLE_GEMINI_API
    request.app.state.config.GEMINI_API_BASE_URLS = form_data.GEMINI_API_BASE_URLS
    request.app.state.config.GEMINI_API_KEYS = form_data.GEMINI_API_KEYS

    # Check if API KEYS length is same than API URLS length
    if len(request.app.state.config.GEMINI_API_KEYS) != len(
        request.app.state.config.GEMINI_API_BASE_URLS
    ):
        if len(request.app.state.config.GEMINI_API_KEYS) > len(
            request.app.state.config.GEMINI_API_BASE_URLS
        ):
            request.app.state.config.GEMINI_API_KEYS = (
                request.app.state.config.GEMINI_API_KEYS[
                    : len(request.app.state.config.GEMINI_API_BASE_URLS)
                ]
            )
        else:
            request.app.state.config.GEMINI_API_KEYS += [""] * (
                len(request.app.state.config.GEMINI_API_BASE_URLS)
                - len(request.app.state.config.GEMINI_API_KEYS)
            )

    request.app.state.config.GEMINI_API_CONFIGS = form_data.GEMINI_API_CONFIGS

    # Remove the API configs that are not in the API URLS
    keys = list(map(str, range(len(request.app.state.config.GEMINI_API_BASE_URLS))))
    request.app.state.config.GEMINI_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.GEMINI_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_GEMINI_API": request.app.state.config.ENABLE_GEMINI_API,
        "GEMINI_API_BASE_URLS": request.app.state.config.GEMINI_API_BASE_URLS,
        "GEMINI_API_KEYS": request.app.state.config.GEMINI_API_KEYS,
        "GEMINI_API_CONFIGS": request.app.state.config.GEMINI_API_CONFIGS,
    }


async def get_all_models_responses(request: Request, user: UserModel) -> list:
    if not request.app.state.config.ENABLE_GEMINI_API:
        return []

    # Check if API KEYS length is same than API URLS length
    num_urls = len(request.app.state.config.GEMINI_API_BASE_URLS)
    num_keys = len(request.app.state.config.GEMINI_API_KEYS)

    if num_keys != num_urls:
        if num_keys > num_urls:
            new_keys = request.app.state.config.GEMINI_API_KEYS[:num_urls]
            request.app.state.config.GEMINI_API_KEYS = new_keys
        else:
            request.app.state.config.GEMINI_API_KEYS += [""] * (num_urls - num_keys)

    request_tasks = []
    for idx, url in enumerate(request.app.state.config.GEMINI_API_BASE_URLS):
        if (str(idx) not in request.app.state.config.GEMINI_API_CONFIGS) and (
            url not in request.app.state.config.GEMINI_API_CONFIGS
        ):
            request_tasks.append(
                send_get_request(
                    f"{url}/models",
                    request.app.state.config.GEMINI_API_KEYS[idx],
                    user=user,
                )
            )
        else:
            api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.GEMINI_API_CONFIGS.get(url, {}),
            )

            enable = api_config.get("enable", True)
            model_ids = api_config.get("model_ids", [])

            if enable:
                if len(model_ids) == 0:
                    request_tasks.append(
                        send_get_request(
                            f"{url}/models",
                            request.app.state.config.GEMINI_API_KEYS[idx],
                            user=user,
                        )
                    )
                else:
                    request_tasks.append(asyncio.create_task(asyncio.sleep(0)))
            else:
                request_tasks.append(asyncio.create_task(asyncio.sleep(0)))

    responses = await asyncio.gather(*request_tasks)
    return responses


@router.get("/models")
@router.get("/models/{url_idx}")
@cached(ttl=MODELS_CACHE_TTL)
async def get_models(
    request: Request, url_idx: Optional[int] = None, user=Depends(get_verified_user)
):
    if not request.app.state.config.ENABLE_GEMINI_API:
        return {"data": []}

    models = []

    if url_idx is None:
        # Get models from all configured URLs
        responses = await get_all_models_responses(request, user)

        for idx, response in enumerate(responses):
            if response:
                url = request.app.state.config.GEMINI_API_BASE_URLS[idx]
                api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
                    str(idx),
                    request.app.state.config.GEMINI_API_CONFIGS.get(url, {}),
                )

                prefix_id = api_config.get("prefix_id", None)
                model_ids = api_config.get("model_ids", [])

                if "models" in response:
                    for model in response["models"]:
                        model_id = model.get("name", "").replace("models/", "")
                        if len(model_ids) == 0 or model_id in model_ids:
                            if prefix_id:
                                model_id = f"{prefix_id}.{model_id}"

                            models.append(
                                {
                                    "id": model_id,
                                    "name": model.get("displayName", model_id),
                                    "object": "model",
                                    "created": 0,
                                    "owned_by": "google",
                                    "gemini": {
                                        "name": model.get("name", ""),
                                        "description": model.get("description", ""),
                                        "version": model.get("version", ""),
                                    },
                                }
                            )
    else:
        # Get models from a specific URL index
        if url_idx >= len(request.app.state.config.GEMINI_API_BASE_URLS):
            raise HTTPException(
                status_code=404,
                detail=f"URL index {url_idx} not found",
            )

        url = request.app.state.config.GEMINI_API_BASE_URLS[url_idx]
        key = request.app.state.config.GEMINI_API_KEYS[url_idx]
        api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
            str(url_idx),
            request.app.state.config.GEMINI_API_CONFIGS.get(url, {}),
        )

        prefix_id = api_config.get("prefix_id", None)
        model_ids = api_config.get("model_ids", [])

        response = await send_get_request(f"{url}/models", key, user=user)

        if response and "models" in response:
            for model in response["models"]:
                model_id = model.get("name", "").replace("models/", "")
                if len(model_ids) == 0 or model_id in model_ids:
                    if prefix_id:
                        model_id = f"{prefix_id}.{model_id}"

                    models.append(
                        {
                            "id": model_id,
                            "name": model.get("displayName", model_id),
                            "object": "model",
                            "created": 0,
                            "owned_by": "google",
                            "gemini": {
                                "name": model.get("name", ""),
                                "description": model.get("description", ""),
                                "version": model.get("version", ""),
                            },
                        }
                    )

    return {"data": models}


def convert_openai_to_gemini_payload(openai_payload):
    """Convert OpenAI-style payload to Gemini API format"""
    gemini_payload = {
        "contents": [],
        "generationConfig": {},
    }

    # Convert messages to Gemini contents format
    for msg in openai_payload.get("messages", []):
        role = msg.get("role")
        content = msg.get("content", "")

        if role == "system":
            # Gemini uses systemInstruction separately
            gemini_payload["systemInstruction"] = {
                "parts": [{"text": content}]
            }
        else:
            # Map OpenAI roles to Gemini roles
            gemini_role = "user" if role in ["user", "assistant"] else "user"
            if role == "assistant":
                gemini_role = "model"

            gemini_payload["contents"].append({
                "role": gemini_role,
                "parts": [{"text": content}]
            })

    # Map generation parameters
    gen_config = gemini_payload["generationConfig"]
    
    if "max_tokens" in openai_payload:
        gen_config["maxOutputTokens"] = openai_payload["max_tokens"]
    
    if "temperature" in openai_payload:
        gen_config["temperature"] = openai_payload["temperature"]
    
    if "top_p" in openai_payload:
        gen_config["topP"] = openai_payload["top_p"]
    
    if "stop" in openai_payload:
        stop_sequences = openai_payload["stop"]
        if isinstance(stop_sequences, str):
            stop_sequences = [stop_sequences]
        gen_config["stopSequences"] = stop_sequences

    # Gemini-specific parameters
    if "top_k" in openai_payload:
        gen_config["topK"] = openai_payload["top_k"]

    return gemini_payload


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

    # Get model from cache
    if not hasattr(request.app.state, "GEMINI_MODELS"):
        request.app.state.GEMINI_MODELS = {}

    # Fetch models if not cached
    if not request.app.state.GEMINI_MODELS:
        models_response = await get_models(request, user)
        for model in models_response.get("data", []):
            request.app.state.GEMINI_MODELS[model["id"]] = {
                "id": model["id"],
                "name": model.get("name", model["id"]),
                "urlIdx": 0,
            }

    model = request.app.state.GEMINI_MODELS.get(model_id)
    if model:
        idx = model.get("urlIdx", 0)
    else:
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    # Get the API config for the model
    api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.GEMINI_API_CONFIGS.get(
            request.app.state.config.GEMINI_API_BASE_URLS[idx], {}
        ),
    )

    prefix_id = api_config.get("prefix_id", None)
    if prefix_id:
        payload["model"] = payload["model"].replace(f"{prefix_id}.", "")

    url = request.app.state.config.GEMINI_API_BASE_URLS[idx]
    key = request.app.state.config.GEMINI_API_KEYS[idx]

    # Convert OpenAI format to Gemini format
    gemini_payload = convert_openai_to_gemini_payload(payload)
    
    # Determine if streaming
    is_streaming = payload.get("stream", False)
    
    # Build request URL - use streamGenerateContent for streaming
    model_name = payload["model"]
    if "/" not in model_name:
        model_name = f"models/{model_name}"
    
    if is_streaming:
        request_url = f"{url}/{model_name}:streamGenerateContent?alt=sse&key={key}"
    else:
        request_url = f"{url}/{model_name}:generateContent?key={key}"

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, metadata, user=user
    )

    # Remove x-goog-api-key from headers as we're using query param
    headers.pop("x-goog-api-key", None)

    payload_json = json.dumps(gemini_payload)

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
            
            # Convert Gemini response to OpenAI format
            openai_response = {
                "id": f"chatcmpl-{hashlib.sha256(json.dumps(response_data).encode()).hexdigest()[:8]}",
                "object": "chat.completion",
                "created": 0,
                "model": model_id,
                "choices": [],
            }

            if "candidates" in response_data and len(response_data["candidates"]) > 0:
                candidate = response_data["candidates"][0]
                content = ""
                
                if "content" in candidate and "parts" in candidate["content"]:
                    for part in candidate["content"]["parts"]:
                        if "text" in part:
                            content += part["text"]

                openai_response["choices"].append({
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": candidate.get("finishReason", "stop").lower(),
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
