from dataclasses import dataclass
from functools import lru_cache
from typing import TypeVar

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models import FilmShort, Genre, Person
from models.search import SearchResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from services.base import BaseService
from services.repositories.search import SearchElasticRepository

T = TypeVar("T", bound=FilmShort | Genre | Person)


@dataclass
class IndexMetaData:
    search_fields: list[str]
    response_type: type[BaseModel]


INDEX_SEARCH_FIELDS: dict[str, IndexMetaData] = {
    EsIndexes.movies.value: IndexMetaData(
        search_fields=["title"],
        response_type=FilmShort,
    ),
    EsIndexes.genres.value: IndexMetaData(
        search_fields=["name"],
        response_type=Genre,
    ),
    EsIndexes.persons.value: IndexMetaData(
        search_fields=["full_name"],
        response_type=Person,
    ),
}


class SearchService(BaseService):
    async def search(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse[T]:
        result = await self.get_data_from_cache(
            SearchResponse,
            True,
            query_string=query_string,
            page_size=page_size,
            page_number=page_number,
        )
        if not result:
            result = await self.repository.get_search_result(
                query_string=query_string,
                page_size=page_size,
                page_number=page_number,
            )
            if result:
                await self.put_into_cache(
                    result,
                    query_string=query_string,
                    page_size=page_size,
                    page_number=page_number,
                )
        return result


@lru_cache()
def get_films_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    repository = SearchElasticRepository[FilmShort](
        EsIndexes.movies.value, elastic
    )
    return SearchService(
        repository=repository,
        cache_service=redis,
        key_prefix=EsIndexes.movies.value,
        cache_expire=settings.film_cache_expire_in_seconds,
    )


@lru_cache()
def get_genres_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    repository = SearchElasticRepository[Genre](
        EsIndexes.genres.value, elastic
    )
    return SearchService(
        repository=repository,
        cache_service=redis,
        key_prefix=EsIndexes.genres.value,
        cache_expire=settings.genre_cache_expire_in_seconds,
    )


@lru_cache()
def get_persons_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    repository = SearchElasticRepository[Person](
        EsIndexes.persons.value, elastic
    )
    return SearchService(
        repository=repository,
        cache_service=redis,
        key_prefix=EsIndexes.persons.value,
        cache_expire=settings.person_cache_expire_in_seconds,
    )
