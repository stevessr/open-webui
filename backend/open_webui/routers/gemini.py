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
    AIOHTTP_CLIENT_TIMEOUT_STREAMING,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.models.users import UserModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import SRC_LOG_LEVELS


from open_webui.utils.payload import (
    apply_model_params_to_body_openai,
    apply_system_prompt_to_body,
    convert_openai_tool_choice_to_gemini,
    convert_openai_tools_to_gemini,
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
                    **({"x-goog-api-key": f"{key}"} if key else {}),
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
    }

    # Gemini usually uses key as query param but can be in header too depending on implementation
    # Standard Google AI Studio uses query param ?key=API_KEY

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


@router.get("/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    if not request.app.state.config.ENABLE_GEMINI_API:
        return {"data": []}

    # Check if API KEYS length is same than API URLS length
    num_urls = len(request.app.state.config.GEMINI_API_BASE_URLS)
    num_keys = len(request.app.state.config.GEMINI_API_KEYS)

    if num_keys != num_urls:
        # if there are more keys than urls, remove the extra keys
        if num_keys > num_urls:
            new_keys = request.app.state.config.GEMINI_API_KEYS[:num_urls]
            request.app.state.config.GEMINI_API_KEYS = new_keys
        # if there are more urls than keys, add empty keys
        else:
            request.app.state.config.GEMINI_API_KEYS += [""] * (num_urls - num_keys)

    request_tasks = []
    for idx, url in enumerate(request.app.state.config.GEMINI_API_BASE_URLS):
        if (str(idx) not in request.app.state.config.GEMINI_API_CONFIGS) and (
            url not in request.app.state.config.GEMINI_API_CONFIGS  # Legacy support
        ):
            # Try to get models from the actual Gemini API
            key = request.app.state.config.GEMINI_API_KEYS[idx]
            if key:
                request_tasks.append(
                    send_get_request(
                        f"{url}/models?key={key}",
                        key,
                        user=user,
                    )
                )
            else:
                request_tasks.append(asyncio.ensure_future(asyncio.sleep(0, None)))
        else:
            api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.GEMINI_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            enable = api_config.get("enable", True)
            model_ids = api_config.get("model_ids", [])

            if enable:
                if len(model_ids) == 0:
                    # Try to get from API if we have a key, otherwise use defaults
                    key = request.app.state.config.GEMINI_API_KEYS[idx]
                    if key:
                        request_tasks.append(
                            send_get_request(
                                f"{url}/models?key={key}",
                                key,
                                user=user,
                            )
                        )
                    else:
                        # Default Gemini models if no key specified
                        model_list = {
                            "object": "list",
                            "data": [
                                {
                                    "id": "gemini-1.5-pro-latest",
                                    "name": "Gemini 1.5 Pro",
                                    "owned_by": "google",
                                    "gemini": {"id": "gemini-1.5-pro-latest"},
                                    "urlIdx": idx,
                                },
                                {
                                    "id": "gemini-1.5-flash-latest",
                                    "name": "Gemini 1.5 Flash",
                                    "owned_by": "google",
                                    "gemini": {"id": "gemini-1.5-flash-latest"},
                                    "urlIdx": idx,
                                },
                                {
                                    "id": "gemini-pro",
                                    "name": "Gemini Pro",
                                    "owned_by": "google",
                                    "gemini": {"id": "gemini-pro"},
                                    "urlIdx": idx,
                                },
                            ],
                        }
                        request_tasks.append(
                            asyncio.ensure_future(asyncio.sleep(0, model_list))
                        )
                else:
                    model_list = {
                        "object": "list",
                        "data": [
                            {
                                "id": model_id,
                                "name": model_id,
                                "owned_by": "google",
                                "gemini": {"id": model_id},
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
        # Gemini API returns 'models' instead of 'data'
        if response and "models" in response:
            return response["models"]
        if response and "data" in response:
            return response["data"]
        if isinstance(response, list):
            return response
        return None

    def filter_gemini_models(models_data):
        """Filter to only include generative models"""
        if not isinstance(models_data, list):
            return []

        generative_models = []
        for model in models_data:
            model_id = model.get("name", "").split("/")[
                -1
            ]  # Extract model name from full path
            # Only include models that support generateContent
            if any(keyword in model_id.lower() for keyword in ["gemini"]):
                generative_models.append(
                    {
                        "id": model_id,
                        "name": model.get("displayName", model_id),
                        "owned_by": "google",
                        "gemini": {"id": model_id},
                        **model,
                    }
                )
        return generative_models

    def get_merged_models(model_lists):
        models = {}
        for idx, model_list in enumerate(model_lists):
            if model_list is not None and "error" not in model_list:
                for model in model_list:
                    model_id = model.get("id") or model.get("name")
                    if model_id and model_id not in models:
                        # Gemini API returns 'displayName' instead of 'name'
                        model_name = (
                            model.get("displayName") or model.get("name") or model_id
                        )

                        # Remove 'models/' prefix if present for cleaner ID
                        if model_id.startswith("models/"):
                            clean_id = model_id.replace("models/", "")
                        else:
                            clean_id = model_id

                        if isinstance(model_name, str) and model_name.startswith("models/"):
                            model_name = model_name.replace("models/", "")

                        models[clean_id] = {
                            **model,
                            "id": clean_id,
                            "name": model_name,
                            "owned_by": "gemini",
                            "gemini": {
                                **model,
                                "original_id": model_id,  # Store original ID with models/ prefix
                            },
                            "connection_type": model.get("connection_type", "external"),
                            "urlIdx": idx,
                        }
        return models

    models = get_merged_models(map(extract_data, responses))
    request.app.state.GEMINI_MODELS = models

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


@router.post("/models/{model}:generateContent")
async def generate_content(
    model: str,
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    """Direct Gemini-style generateContent endpoint"""
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    # For now we just use the first available config/key
    idx = 0

    # Get the API config for the model
    api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.GEMINI_API_CONFIGS.get(
            request.app.state.config.GEMINI_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.GEMINI_API_BASE_URLS[idx]
    key = request.app.state.config.GEMINI_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, user=user
    )

    # Use the form_data directly as it's already in Gemini format
    gemini_payload = form_data

    if "tools" in gemini_payload:
        gemini_payload["tools"] = convert_openai_tools_to_gemini(
            gemini_payload["tools"]
        )

    if "tool_choice" in gemini_payload and "tool_config" not in gemini_payload:
        tool_config = convert_openai_tool_choice_to_gemini(
            gemini_payload["tool_choice"]
        )
        if tool_config:
            gemini_payload["tool_config"] = tool_config

    # Construct the direct Gemini API URL
    request_url = f"{url}/models/{model}:generateContent?key={key}"
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
        raise HTTPException(
            status_code=r.status if r else 500,
            detail="Open WebUI: Server Connection Error",
        )
    finally:
        await cleanup_response(r, session)


@router.post("/models/{model}:streamGenerateContent")
async def stream_generate_content(
    model: str,
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    """Direct Gemini-style streamGenerateContent endpoint"""
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    # For now we just use the first available config/key
    idx = 0

    # Get the API config for the model
    api_config = request.app.state.config.GEMINI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.GEMINI_API_CONFIGS.get(
            request.app.state.config.GEMINI_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.GEMINI_API_BASE_URLS[idx]
    key = request.app.state.config.GEMINI_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, user=user
    )

    # Use the form_data directly as it's already in Gemini format
    gemini_payload = form_data

    if "tools" in gemini_payload:
        gemini_payload["tools"] = convert_openai_tools_to_gemini(
            gemini_payload["tools"]
        )

    if "tool_choice" in gemini_payload and "tool_config" not in gemini_payload:
        tool_config = convert_openai_tool_choice_to_gemini(
            gemini_payload["tool_choice"]
        )
        if tool_config:
            gemini_payload["tool_config"] = tool_config

    # Construct the direct Gemini API URL
    request_url = f"{url}/models/{model}:streamGenerateContent?key={key}"
    payload_json = json.dumps(gemini_payload)

    r = None
    session = None

    try:
        session = aiohttp.ClientSession(
            trust_env=True,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_STREAMING),
        )

        r = await session.request(
            method="POST",
            url=request_url,
            data=payload_json,
            headers=headers,
            cookies=cookies,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )

        # Return the raw stream directly from Gemini
        return StreamingResponse(
            r.content,
            status_code=r.status,
            headers=dict(r.headers),
            background=BackgroundTask(cleanup_response, response=r, session=session),
        )

    except Exception as e:
        log.exception(e)
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

    async with aiohttp.ClientSession(
        trust_env=True,
        timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST),
    ) as session:
        try:
            # Verify using get models or simple generation
            # https://generativelanguage.googleapis.com/v1beta/models?key=API_KEY

            async with session.get(
                f"{url}/models?key={key}",
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
