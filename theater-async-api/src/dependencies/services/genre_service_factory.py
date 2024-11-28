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
from services.genre import GenreService


@lru_cache()
def get_genre_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> GenreService:
    repository = get_repository(GenreService, db_service)
    return GenreService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="genre",
        cache_expire=settings.genre_cache_expire_in_seconds,
    )
