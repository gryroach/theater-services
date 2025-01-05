import logging
import os
from logging import config as logging_config

from core.logger import LOGGING
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logging_config.dictConfig(LOGGING)

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_log_level(level_name):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)


class Settings(BaseSettings):
    # Логирование
    console_log_level: str = Field(default="INFO", alias="CONSOLE_LOG_LEVEL")

    # Название проекта. Используется в Swagger-документации
    project_name: str = Field(
        default="Read-only API для онлайн-кинотеатра", alias="PROJECT_NAME"
    )

    # Настройки Redis
    redis_host: str = Field(default="127.0.0.1", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")

    # Настройки Elasticsearch
    elastic_host: str = Field(default="127.0.0.1", alias="ELASTIC_HOST")
    elastic_port: int = Field(default=9200, alias="ELASTIC_PORT")
    elastic_schema: str = Field(default="http://", alias="ELASTIC_SCHEMA")

    # Кеширование
    film_cache_expire_in_seconds: int = Field(
        default=60 * 5, alias="FILM_CACHE_EXPIRE_IN_SECONDS"
    )
    person_cache_expire_in_seconds: int = Field(
        default=60 * 10, alias="PERSON_CACHE_EXPIRE_IN_SECONDS"
    )
    genre_cache_expire_in_seconds: int = Field(
        default=60 * 20, alias="GENRE_CACHE_EXPIRE_IN_SECONDS"
    )

    # Трассировка
    jaeger_host: str = Field(default="jaeger")
    jaeger_port: int = Field(default=6831)

    # Авторизация
    jwt_algorithm: str = Field(default="RS256")
    jwt_public_key_path: str = Field(default="/app/keys/public_key.pem")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def elasticsearch_url(self) -> str:
        return f"{self.elastic_schema}{self.elastic_host}:{self.elastic_port}"

    @property
    def jwt_public_key(self) -> str:
        try:
            with open(self.jwt_public_key_path, "r") as key_file:
                return key_file.read()
        except FileNotFoundError:
            raise ValueError(
                f"Public key file not found at: {self.jwt_public_key_path}"
            )
        except Exception as e:
            raise ValueError(f"Error reading public key: {str(e)}")


settings = Settings()

logging.basicConfig(
    level=get_log_level(settings.console_log_level),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
