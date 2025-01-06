from fastapi import APIRouter

from .google import router as google_router

router = APIRouter()

router.include_router(
    google_router,
    prefix="/google",
    tags=["Аутентификация через google"],
)
