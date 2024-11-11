from contextlib import asynccontextmanager

from api.v1 import genre, person
from core import config
from db import elastic, redis
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    elastic.es = AsyncElasticsearch(
        hosts=[
            f"{config.ELASTIC_SCHEMA}{config.ELASTIC_HOST}:{config.ELASTIC_PORT}"
        ]
    )
    yield
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    title=config.PROJECT_NAME,
    description="Информация о фильмах, жанрах и людях, участвовавших в создании произведения",
    version="1.0.0",
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)

app.include_router(person.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(genre.router, prefix="/api/v1/genres", tags=["genres"])
