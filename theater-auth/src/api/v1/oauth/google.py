from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from starlette.responses import RedirectResponse

from db.db import get_session
from exceptions.auth_exceptions import AuthError
from schemas.login import LoginResponse
from schemas.user import UserEmailRegister
from services.auth import AuthService, get_auth_service
from services.oauth.google import get_authorization_url, get_google_id_info
from services.user import UserService, get_user_service

router = APIRouter()


@router.get(
    "/login",
    response_model=None,
    status_code=status.HTTP_200_OK,
    description=(
        "Аутентификация пользователя через Google. "
        "Не работает в swagger-окружении."
    ),
    summary="Аутентификация пользователя через Google",
)
async def login():
    return RedirectResponse(get_authorization_url()[0])


@router.get(
    "/callback",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    description=(
        "Коллбэк для получения токенов доступа через Google. "
        "Если пользователя не существует, то он создается."
    ),
    summary="Коллбэк для получения токенов доступа через Google",
)
async def callback_google(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_session)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    try:
        id_info = get_google_id_info(str(request.url))
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )

    first_name = id_info.get("given_name", "")
    last_name = id_info.get("family_name", "")
    email = id_info.get("email")

    user = await user_service.register_user_by_email(
        db,
        UserEmailRegister(
            first_name=first_name, last_name=last_name, email=email
        ),
    )
    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    tokens = await auth_service.login(
        db,
        user.login,
        user.password,
        ip_address,
        user_agent,
        user,
    )
    return tokens
