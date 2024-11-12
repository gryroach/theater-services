import logging
import os
from logging import config as logging_config

from dotenv import load_dotenv

from core.logger import LOGGING

load_dotenv()
logging_config.dictConfig(LOGGING)


def get_log_level(level_name):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)


logging.basicConfig(
    level=get_log_level(os.getenv("CONSOLE_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv("PROJECT_NAME", "Read-only API для онлайн-кинотеатра")

# Настройки Redis
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Настройки Elasticsearch
ELASTIC_HOST = os.getenv("ES_HOST", "127.0.0.1")
ELASTIC_PORT = int(os.getenv("ES_PORT", 9200))
ELASTIC_SCHEMA = os.getenv("ELASTIC_SCHEMA", "http://")

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Кеширование
FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут
PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 10  # 10 минут
GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 20  # 20 минут
