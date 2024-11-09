import logging
import os
from contextlib import asynccontextmanager

from api.v1 import films, genre, person
from core import config
from db import elastic, redis
from dotenv import load_dotenv
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis

# Загружаем переменные окружения из файла .env
load_dotenv()


# Функция для преобразования строкового уровня в объект уровня логирования
def get_log_level(level_name):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)  # По умолчанию INFO


logging.basicConfig(
    level=get_log_level(os.getenv("CONSOLE_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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

app.include_router(films.router, prefix="/api/v1/films", tags=["films"])
app.include_router(person.router, prefix="/api/v1/persons", tags=["persons"])
app.include_router(genre.router, prefix="/api/v1/genres", tags=["genres"])
