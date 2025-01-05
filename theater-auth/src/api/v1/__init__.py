from fastapi import APIRouter

from .auth import router as auth_router
from .oauth import router as oauth_router
from .inspection import router as inspect_router
from .profile import router as profile_router
from .user import router as user_router

api_router = APIRouter()

api_router.include_router(
    inspect_router,
    prefix="/inspect",
    tags=["Проверка сервисов"],
)
api_router.include_router(
    user_router,
    prefix="/users",
    tags=["API для управления пользователями"],
)
api_router.include_router(
    profile_router,
    prefix="/profile",
    tags=["API личного кабинета"],
)
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["API аутентификации"],
)
api_router.include_router(
    oauth_router,
    prefix="/oauth",
)
