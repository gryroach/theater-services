from contextlib import asynccontextmanager

from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

from api.v1 import films
from core import config
from db import elastic, redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis.redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT)
    elastic.es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_SCHEMA}{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])
    yield
    await redis.redis.close()
    await elastic.es.close()


app = FastAPI(
    title=config.PROJECT_NAME,
    description='Информация о фильмах, жанрах и людях, участвовавших в создании произведения',
    version="1.0.0",
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
    lifespan=lifespan
)

app.include_router(films.router, prefix='/api/v1/films', tags=['films'])
