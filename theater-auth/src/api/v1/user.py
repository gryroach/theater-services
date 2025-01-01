from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.db import get_session
from dependencies.auth import require_roles
from exceptions.user_exceptions import UserDoesNotExistsError
from schemas.base import ErrorResponse
from schemas.role import Role, UpdateRole
from services.roles import Roles
from services.user import UserService, get_user_service

router = APIRouter()


@router.get(
    "/{user_id}/role",
    response_model=Role,
    status_code=status.HTTP_200_OK,
    description="Получение роли пользователя",
    summary="Получение роли пользователя",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User not found",
        }
    },
    dependencies=[
        Depends(require_roles([Roles.admin.name, Roles.moderator.name]))
    ],
)
async def get_user_role(
    user_id: UUID,
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Role:
    try:
        role = await user_service.get_user_role(db, user_id)
    except UserDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    return role


@router.patch(
    "/{user_id}/role",
    response_model=Role,
    status_code=status.HTTP_200_OK,
    description="Изменение роли пользователя",
    summary="Изменение роли пользователя",
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "User not found",
        }
    },
    dependencies=[
        Depends(require_roles([Roles.admin.name, Roles.moderator.name]))
    ],
)
async def set_user_role(
    user_id: UUID,
    role: UpdateRole,
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> Role:
    try:
        role = await user_service.update_role(db, user_id, role)
    except UserDoesNotExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    return role
