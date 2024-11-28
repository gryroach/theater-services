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
from services.person import PersonService


@lru_cache()
def get_person_service(
    cache_service: CacheServiceInterface = Depends(get_cache_service),
    db_service: DatabaseServiceInterface = Depends(get_db_service),
) -> PersonService:
    repository = get_repository(PersonService, db_service)
    return PersonService(
        repository=repository,
        cache_service=cache_service,
        key_prefix="person",
        cache_expire=settings.person_cache_expire_in_seconds,
    )
