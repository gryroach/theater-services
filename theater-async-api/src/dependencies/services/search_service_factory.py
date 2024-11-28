from functools import lru_cache

from fastapi import Depends

from core.config import settings
from dependencies.base import (
    DatabaseServiceInterface,
    get_cache_service,
    get_db_service,
    get_repository,
)
from models import FilmShort, Genre, Person
from services.base import CacheServiceInterface
from services.search import SearchService


@lru_cache()
def get_films_search_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> SearchService:
    repository = get_repository(SearchService[FilmShort], db_service)
    return SearchService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="movie",
        cache_expire=settings.film_cache_expire_in_seconds,
    )


@lru_cache()
def get_genres_search_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> SearchService:
    repository = get_repository(SearchService[Genre], db_service)
    return SearchService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="genre",
        cache_expire=settings.genre_cache_expire_in_seconds,
    )


@lru_cache()
def get_persons_search_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> SearchService:
    repository = get_repository(SearchService[Person], db_service)
    return SearchService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="person",
        cache_expire=settings.person_cache_expire_in_seconds,
    )
