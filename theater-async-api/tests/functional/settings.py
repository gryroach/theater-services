from dotenv import find_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from .testdata.index_mappings import (
    genres_schema,
    movies_schema,
    persons_schema,
)

DOTENV_PATH = find_dotenv(".env.tests")


class TestSettings(BaseSettings):
    # API
    service_url: str = Field(
        default="http://127.0.0.1:5000",
        alias="TESTS_SERVICE_URL",
    )

    # Настройки Redis
    redis_host: str = Field(
        default="127.0.0.1",
        alias="TESTS_REDIS_HOST",
    )
    redis_port: int = Field(
        default=6379,
        alias="TESTS_REDIS_PORT",
    )

    # Настройки Elasticsearch
    elastic_host: str = Field(
        default="127.0.0.1",
        alias="TESTS_ELASTIC_HOST",
    )
    elastic_port: int = Field(
        default=9200,
        alias="TESTS_ELASTIC_PORT",
    )
    elastic_schema: str = Field(
        default="http://",
        alias="TESTS_ELASTIC_SCHEMA",
    )

    model_config = SettingsConfigDict(
        env_file=DOTENV_PATH,
        env_file_encoding="utf-8",
        env_prefix="TESTS_",
        extra="ignore",
    )

    @property
    def elasticsearch_url(self) -> str:
        return f"{self.elastic_schema}{self.elastic_host}:{self.elastic_port}"


class EsBaseSettings(BaseSettings):
    es_id_field: str = "_id"


class MoviesSettings(EsBaseSettings):
    es_index: str = "movies"
    es_index_mapping: dict = movies_schema


class GenresSettings(EsBaseSettings):
    es_index: str = "genres"
    es_index_mapping: dict = genres_schema


class PersonsSettings(EsBaseSettings):
    es_index: str = "persons"
    es_index_mapping: dict = persons_schema


test_settings = TestSettings()
es_movies_settings = MoviesSettings()
es_genres_settings = GenresSettings()
es_persons_settings = PersonsSettings()
