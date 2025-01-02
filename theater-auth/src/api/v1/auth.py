from typing import Annotated

from db.db import get_session
from dependencies.auth import JWTBearer, get_current_user
from fastapi import APIRouter, Depends, Request
from schemas.login import LoginHistoryInDB, LoginRequest, LoginResponse
from schemas.paginator import PaginationResult, Paginator
from schemas.refresh import TokenRefreshRequest, TokenResponse
from schemas.user import UserInDB, UserRegister
from services.auth import AuthService, get_auth_service
from services.login_history import (
    LoginHistoryService,
    get_login_history_service,
)
from services.user import UserService, get_user_service
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    description="Аутентификация пользователя",
    summary="Аутентификация пользователя",
)
async def login(
    request: Request,
    login_request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Аутентификация пользователя."""
    ip_address = request.client.host
    user_agent = request.headers.get("User-Agent", "")
    tokens = await auth_service.login(
        db,
        login_request.login,
        login_request.password,
        ip_address,
        user_agent,
    )
    return tokens


@router.get(
    "/login-history",
    response_model=PaginationResult[LoginHistoryInDB],
    description="История входов",
    summary="История входов",
)
async def get_login_history(
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    history_service: Annotated[
        LoginHistoryService, Depends(get_login_history_service)
    ],
    paginator: Annotated[Paginator[LoginHistoryInDB], Depends()],
):
    """Получить историю входов текущего пользователя с пагинацией."""
    history = await history_service.get_user_history(
        db,
        user_id=str(current_user.id),
        skip=paginator.skip,
        limit=paginator.size,
    )
    return paginator.to_response(data=history)


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    description="Выход из текущей сессии",
    summary="Выход из текущей сессии",
    dependencies=[Depends(JWTBearer())],
)
async def logout(
    logout_token_request: TokenRefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    """
    Выход из текущей сессии. Инвалидация токена.
    """
    await auth_service.logout(
        refresh_token=logout_token_request.refresh_token,
    )
    return {"message": "Successfully logged out from the current session."}


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    description="Обновление токенов",
    summary="Обновление токенов",
)
async def refresh_tokens(
    refresh_request: TokenRefreshRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """
    Обновляет Access-токен с использованием валидного Refresh-токена.
    """
    new_tokens = await auth_service.refresh_tokens(
        refresh_token=refresh_request.refresh_token
    )
    return new_tokens


@router.post(
    "/logout/all",
    status_code=status.HTTP_200_OK,
    description="Выход из всех устройств",
    summary="Выход из всех устройств",
)
async def logout_all_devices(
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> dict:
    """
    Выход из всех устройств, инвалидация всех токенов пользователя.
    """
    await auth_service.logout_all(user_id=str(current_user.id))
    return {
        "message": "Successfully logged out from all devices.",
        "user_id": current_user.id,
    }


@router.post(
    "/signup",
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    description="Регистрация пользователя",
    summary="Регистрация пользователя",
)
async def create_user(
    user_create: UserRegister,
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserInDB:
    """Регистрация пользователя."""
    user = await user_service.register_user(db, user_create)
    return user
