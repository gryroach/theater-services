from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from redis.asyncio import Redis

from api.v1.base import api_router as api_v1_router
from core.config import settings
from core.tracer import configure_tracer
from db import elastic, redis
from middlewares.tracing import request_id_span


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracer()
    redis.redis = Redis(host=settings.redis_host, port=settings.redis_port)
    elastic.es = AsyncElasticsearch(hosts=[settings.elasticsearch_url])
    yield
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    title=settings.project_name,
    description=(
        "Информация о фильмах, жанрах и людях, "
        "участвовавших в создании произведения"
    ),
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

FastAPIInstrumentor.instrument_app(app)

app.middleware("http")(request_id_span)

app.include_router(api_v1_router, prefix="/api/v1")
