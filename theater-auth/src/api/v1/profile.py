from typing import Annotated

from db.db import get_session
from dependencies.auth import JWTBearer, get_current_user
from fastapi import APIRouter, Depends, HTTPException
from schemas.jwt import JwtTokenPayload
from schemas.role import Role
from schemas.user import (
    UserCredentialsUpdate,
    UserData,
    UserInDB,
    UserProfileInfo,
)
from services.roles import Roles
from services.session_service import SessionService, get_session_service
from services.user import UserService, get_user_service
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

router = APIRouter()


@router.patch(
    "/change-credentials",
    response_model=UserInDB,
    status_code=status.HTTP_200_OK,
    summary="Изменение логина и пароля пользователя",
    description=(
        "Изменение логина и пароля пользователя. "
        "После изменения происходит выход из всех устройств."
    ),
)
async def update_credentials(
    user_credentials: UserCredentialsUpdate,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
    session_service: Annotated[SessionService, Depends(get_session_service)],
) -> UserInDB:
    user = await user_service.update_credentials(
        db,
        current_user.id,
        user_credentials,
    )
    await session_service.increment_session_version(str(current_user.id))
    return user


@router.patch(
    "/change-user-data",
    response_model=UserData,
    status_code=status.HTTP_200_OK,
    description="Изменение пользовательских данных",
    summary="Изменение пользовательских данных",
)
async def update_user_data(
    user_data: UserData,
    user_service: Annotated[UserService, Depends(get_user_service)],
    current_user: Annotated[UserInDB, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserData:
    user = await user_service.update_user_data(
        db,
        current_user.id,
        user_data,
    )
    return user


@router.get(
    "/permissions",
    response_model=Role,
    status_code=status.HTTP_200_OK,
    description="Получение роли и прав пользователя",
    summary="Получение роли и прав пользователя",
)
async def get_user_permission(
    token_payload: Annotated[JwtTokenPayload, Depends(JWTBearer())],
) -> Role:
    role = getattr(Roles, token_payload.role, None)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid role",
        )
    return role


@router.get(
    "/info",
    response_model=UserProfileInfo,
    status_code=status.HTTP_200_OK,
    summary="Получение информации о пользователе",
    description="Возвращает минимальный набор данных для обновления или создания пользователя в Django.",
)
async def get_profile_info(
    token_payload: Annotated[JwtTokenPayload, Depends(JWTBearer())],
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserProfileInfo:
    user = await user_service.get_user_by_id(db, user_id=token_payload.user)
    return UserProfileInfo(
        id=user.id,
        login=user.login,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
    )
