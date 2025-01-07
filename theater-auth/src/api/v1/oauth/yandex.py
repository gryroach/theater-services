from typing import Annotated

import httpx
from core.config import settings
from db.db import get_session
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from schemas.login import LoginPasswordResponse
from schemas.user import UserEmailRegister
from schemas.yandex_auth import YandexAuthRequest, YandexRevokeTokenRequest
from services.auth import AuthService, get_auth_service
from services.oauth.yandex import (
    exchange_code_for_tokens,
    get_user_info,
    revoke_token,
)
from services.user import UserService, get_user_service
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

router = APIRouter()


@router.get(
    "/login",
    response_model=None,
    status_code=status.HTTP_200_OK,
    description="Аутентификация пользователя через Yandex.",
    summary="Аутентификация пользователя через Yandex",
)
async def login():
    yandex_auth_url = settings.yandex_redirect_host
    return RedirectResponse(yandex_auth_url)


@router.post(
    "/exchange-code",
    response_model=LoginPasswordResponse,
    status_code=status.HTTP_200_OK,
    description="Обработка кода авторизации от Yandex и регистрация пользователя.",
    summary="Обмен кода на токены и регистрация пользователя через Yandex",
)
async def exchange_code_yandex(
    request: Request,
    request_data: YandexAuthRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    code = request_data.code
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code is required.",
        )
    try:
        tokens = await exchange_code_for_tokens(code)
        user_info = await get_user_info(tokens["access_token"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Authorization failed: {e}",
        )

    login = user_info.get("login")
    if not login:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve user information from Yandex.",
        )

    first_name = user_info.get("first_name", "")
    last_name = user_info.get("last_name", "")

    user, password = await user_service.register_user_by_email(
        db,
        UserEmailRegister(
            first_name=first_name,
            last_name=last_name,
            email=login,
        ),
    )

    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "Unknown")

    tokens = await auth_service.login(
        db,
        user.login,
        user.password,
        ip_address,
        user_agent,
        user,
    )
    return LoginPasswordResponse(password=password, **tokens.model_dump())


@router.post(
    "/revoke-token",
    status_code=status.HTTP_204_NO_CONTENT,
    description="Отзыв токена Yandex OAuth.",
    summary="Отзыв токена Yandex OAuth",
)
async def revoke_yandex_token(
    request_data: YandexRevokeTokenRequest = Body(...),
):
    """
    Обрабатывает отзыв токена через Yandex OAuth.
    """
    try:
        await revoke_token(request_data.access_token)
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Failed to revoke token: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking token: {e}",
        )
