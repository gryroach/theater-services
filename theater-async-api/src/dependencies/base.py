from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from redis import Redis

from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from models import Film, FilmShort, Genre, Person
from services.base import (
    BaseService,
    DatabaseServiceInterface,
    CacheServiceInterface,
)
from services.film import FilmService
from services.genre import GenreService
from services.person import PersonService
from services.repositories import (
    BaseRepositoryProtocol,
    FilmElasticRepository,
    GenreElasticRepository,
    PersonElasticRepository,
    SearchElasticRepository,
)
from services.search import SearchService


@lru_cache()
def get_db_service(
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> DatabaseServiceInterface:
    return elastic


@lru_cache()
def get_cache_service(
        redis: Redis = Depends(get_redis)
) -> CacheServiceInterface:
    return redis


@lru_cache()
def get_repository(
    service: type[BaseService],
    db_service: DatabaseServiceInterface,
) -> BaseRepositoryProtocol:
    repository_map: dict[
        tuple[type[BaseService], DatabaseServiceInterface],
        BaseRepositoryProtocol,
    ] = {
        (FilmService, AsyncElasticsearch): FilmElasticRepository(
            EsIndexes.movies.value,
            db_service,
            Film,
            FilmShort,
        ),
        (GenreService, AsyncElasticsearch): GenreElasticRepository(
            EsIndexes.genres.value,
            db_service,
            Genre,
            Genre,
        ),
        (PersonService, AsyncElasticsearch): PersonElasticRepository(
            EsIndexes.persons.value,
            db_service,
            Person,
            Person,
        ),
        (SearchService[FilmShort], AsyncElasticsearch): (
            SearchElasticRepository[FilmShort](
                EsIndexes.movies.value,
                db_service,
            )
        ),
        (SearchService[Genre], AsyncElasticsearch): (
            SearchElasticRepository[Genre](
                EsIndexes.genres.value,
                db_service,
            )
        ),
        (SearchService[Person], AsyncElasticsearch): (
            SearchElasticRepository[Person](
                EsIndexes.persons.value,
                db_service,
            )
        ),
    }
    return repository_map[(service, type(db_service))]
