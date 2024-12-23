from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from api.v1 import api_router as api_v1_router
from core.config import settings
from db import redis
from handlers import exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis.from_url(settings.redis_url)
    try:
        yield
    finally:
        await redis.redis.aclose()


app = FastAPI(
    title=settings.project_name,
    description="API сервиса авторизации кинотеатра",
    version="1.0.0",
    docs_url="/api-auth/openapi",
    openapi_url="/api-auth/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    exception_handlers=exception_handlers,
)

app.include_router(api_v1_router, prefix="/api-auth/v1")
