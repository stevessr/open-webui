import json
import logging
from typing import Optional

import aiohttp
from fastapi import Depends, HTTPException, Request, APIRouter
from fastapi.responses import (
    StreamingResponse,
    JSONResponse,
    PlainTextResponse,
)
from pydantic import BaseModel

from open_webui.models.models import Models
from open_webui.env import (
    AIOHTTP_CLIENT_SESSION_SSL,
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
)
from open_webui.models.users import UserModel

from open_webui.env import SRC_LOG_LEVELS


from open_webui.utils.payload import (
    apply_model_params_to_body_openai,
    apply_system_prompt_to_body,
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
                    **({"Authorization": f"Bearer {key}"} if key else {}),
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
        **(
            {
                "X-OpenWebUI-User-Name": user.name,
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

    token = None
    auth_type = config.get("auth_type") if config else None

    if auth_type == "bearer" or auth_type is None:
        # Default to bearer if not specified
        token = f"{key}"
    elif auth_type == "none":
        token = None
    elif auth_type == "session":
        cookies = request.cookies
        token = request.state.token.credentials

    if token:
        headers["Authorization"] = f"Bearer {token}"

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
        "ENABLE_RESPONSES_API": request.app.state.config.ENABLE_RESPONSES_API,
        "RESPONSES_API_BASE_URLS": request.app.state.config.RESPONSES_API_BASE_URLS,
        "RESPONSES_API_KEYS": request.app.state.config.RESPONSES_API_KEYS,
        "RESPONSES_API_CONFIGS": request.app.state.config.RESPONSES_API_CONFIGS,
    }


class ResponsesConfigForm(BaseModel):
    ENABLE_RESPONSES_API: Optional[bool] = None
    RESPONSES_API_BASE_URLS: list[str]
    RESPONSES_API_KEYS: list[str]
    RESPONSES_API_CONFIGS: dict


@router.post("/config/update")
async def update_config(
    request: Request, form_data: ResponsesConfigForm, user=Depends(get_admin_user)
):
    # Update the Responses API config
    request.app.state.config.ENABLE_RESPONSES_API = form_data.ENABLE_RESPONSES_API
    request.app.state.config.RESPONSES_API_BASE_URLS = form_data.RESPONSES_API_BASE_URLS
    request.app.state.config.RESPONSES_API_KEYS = form_data.RESPONSES_API_KEYS

    # Check if API KEYS length is same than API URLS length
    if len(request.app.state.config.RESPONSES_API_KEYS) != len(
        request.app.state.config.RESPONSES_API_BASE_URLS
    ):
        if len(request.app.state.config.RESPONSES_API_KEYS) > len(
            request.app.state.config.RESPONSES_API_BASE_URLS
        ):
            request.app.state.config.RESPONSES_API_KEYS = (
                request.app.state.config.RESPONSES_API_KEYS[
                    : len(request.app.state.config.RESPONSES_API_BASE_URLS)
                ]
            )
        else:
            request.app.state.config.RESPONSES_API_KEYS += [""] * (
                len(request.app.state.config.RESPONSES_API_BASE_URLS)
                - len(request.app.state.config.RESPONSES_API_KEYS)
            )

    request.app.state.config.RESPONSES_API_CONFIGS = form_data.RESPONSES_API_CONFIGS

    # Remove the API configs that are not in the API URLS
    keys = list(map(str, range(len(request.app.state.config.RESPONSES_API_BASE_URLS))))
    request.app.state.config.RESPONSES_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.RESPONSES_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_RESPONSES_API": request.app.state.config.ENABLE_RESPONSES_API,
        "RESPONSES_API_BASE_URLS": request.app.state.config.RESPONSES_API_BASE_URLS,
        "RESPONSES_API_KEYS": request.app.state.config.RESPONSES_API_KEYS,
        "RESPONSES_API_CONFIGS": request.app.state.config.RESPONSES_API_CONFIGS,
    }


@router.get("/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    """Get models from Responses API endpoints"""
    if not request.app.state.config.ENABLE_RESPONSES_API:
        return {"data": []}

    models = {"data": []}

    # Fetch models from each configured Responses API URL
    for idx, url in enumerate(request.app.state.config.RESPONSES_API_BASE_URLS):
        # Skip if no URL configured
        if not url or url == "":
            continue

        key = request.app.state.config.RESPONSES_API_KEYS[idx]

        try:
            # Fetch models from this API endpoint
            r = await send_get_request(f"{url}/models", key, user)

            if r and "data" in r:
                # Add each model from this endpoint
                models["data"].extend(r["data"])
        except Exception as e:
            log.error(f"Error fetching models from {url}: {e}")
            continue

    return models


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
            headers, cookies = await get_headers_and_cookies(
                request, url, key, api_config, user=user
            )

            # Try to list models to verify connection
            async with session.get(
                f"{url}/models",
                headers=headers,
                cookies=cookies,
                ssl=AIOHTTP_CLIENT_SESSION_SSL,
            ) as r:
                try:
                    response_data = await r.json()
                except Exception:
                    response_data = await r.text()

                if r.status != 200:
                    if isinstance(response_data, (dict, list)):
                        return JSONResponse(status_code=r.status, content=response_data)
                    else:
                        return PlainTextResponse(
                            status_code=r.status, content=response_data
                        )

                return response_data

        except aiohttp.ClientError as e:
            # ClientError covers all aiohttp requests issues
            log.exception(f"Client error: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Open WebUI: Server Connection Error"
            )
        except Exception as e:
            log.exception(f"Unexpected error: {e}")
            raise HTTPException(
                status_code=500, detail="Open WebUI: Server Connection Error"
            )


@router.post("/chat/completions")
async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    """OpenAI-compatible chat completions endpoint for responses API"""
    # Delegate to the OpenAI router's chat completions endpoint
    from open_webui.routers.openai import (
        generate_chat_completion as openai_chat_completion,
    )

    return await openai_chat_completion(request, form_data, user, bypass_filter)


@router.post("/")
async def create_response(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    """
    OpenAI Responses API endpoint.

    This endpoint supports the OpenAI Responses API format which includes:
    - Background processing with response_id
    - Built-in tools (web search, file search)
    - Code execution capabilities
    - Streaming responses
    """
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

    # For now we just use the first available config/key
    idx = 0

    # Get the API config for the model
    api_config = request.app.state.config.RESPONSES_API_CONFIGS.get(
        str(idx),
        request.app.state.config.RESPONSES_API_CONFIGS.get(
            request.app.state.config.RESPONSES_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.RESPONSES_API_BASE_URLS[idx]
    key = request.app.state.config.RESPONSES_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, metadata, user=user
    )

    # Construct the OpenAI responses API URL
    request_url = f"{url}/responses"
    payload_json = json.dumps(payload)

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


@router.post("/{response_id}/cancel")
async def cancel_response(
    response_id: str,
    request: Request,
    user=Depends(get_verified_user),
):
    """
    Cancel a background response.

    This endpoint cancels a response that was initiated with background=true.
    """
    # For now we just use the first available config/key
    idx = 0

    # Get the API config
    api_config = request.app.state.config.RESPONSES_API_CONFIGS.get(
        str(idx),
        request.app.state.config.RESPONSES_API_CONFIGS.get(
            request.app.state.config.RESPONSES_API_BASE_URLS[idx], {}
        ),
    )

    url = request.app.state.config.RESPONSES_API_BASE_URLS[idx]
    key = request.app.state.config.RESPONSES_API_KEYS[idx]

    headers, cookies = await get_headers_and_cookies(
        request, url, key, api_config, user=user
    )

    # Construct the cancel URL
    request_url = f"{url}/responses/{response_id}/cancel"

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
            headers=headers,
            cookies=cookies,
            ssl=AIOHTTP_CLIENT_SESSION_SSL,
        )

        try:
            response = await r.json()
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
        await cleanup_response(r, session)
