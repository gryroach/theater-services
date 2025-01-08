from fastapi import APIRouter

from .google import router as google_router
from .yandex import router as yandex_router

router = APIRouter()

router.include_router(
    google_router,
    prefix="/google",
    tags=["Аутентификация через google"],
)
router.include_router(
    yandex_router,
    prefix="/yandex",
    tags=["Аутентификация через yandex"],
)
