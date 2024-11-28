from functools import lru_cache

from fastapi import Depends

from core.config import settings
from dependencies.base import (
    DatabaseServiceInterface,
    get_cache_service,
    get_db_service,
    get_repository,
)
from services.base import CacheServiceInterface
from services.film import FilmService


@lru_cache()
def get_film_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> FilmService:
    repository = get_repository(FilmService, db_service)
    return FilmService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="movie",
        cache_expire=settings.film_cache_expire_in_seconds,
    )
