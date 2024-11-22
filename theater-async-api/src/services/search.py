from dataclasses import dataclass
from functools import lru_cache

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models import FilmShort, Genre, Person
from models.search import FilmSearch, GenreSearch, PersonSearch, SearchResponse
from pydantic import BaseModel
from redis.asyncio import Redis
from services.base import BaseService


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
    ) -> FilmSearch | PersonSearch | GenreSearch:
        result = await self.get_data_from_cache(
            SearchResponse,
            single=True,
            query_string=query_string,
            page_size=page_size,
            page_number=page_number,
        )
        if not result:
            result = await self._get_search_result(
                query_string=query_string,
                page_size=page_size,
                page_number=page_number,
            )
            await self.put_into_cache(
                result,
                query_string=query_string,
                page_size=page_size,
                page_number=page_number,
            )
        return result

    async def _get_search_result(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> FilmSearch | PersonSearch | GenreSearch:
        fields = INDEX_SEARCH_FIELDS[self.index_name].search_fields
        response_type = INDEX_SEARCH_FIELDS[self.index_name].response_type
        query = {"multi_match": {"query": query_string, "fields": fields}}
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        es_result = await self.elastic.search(index=self.index_name, body=body)
        return SearchResponse(  # type: ignore
            count=es_result["hits"]["total"]["value"],
            result=[
                response_type(**hit["_source"])
                for hit in es_result["hits"]["hits"]
            ],
        )


@lru_cache()
def get_films_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    return SearchService(
        cache_service=redis,
        elastic=elastic,
        index_name=EsIndexes.movies.value,
        cache_expire=settings.film_cache_expire_in_seconds,
    )


@lru_cache()
def get_genres_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    return SearchService(
        cache_service=redis,
        elastic=elastic,
        index_name=EsIndexes.genres.value,
        cache_expire=settings.genre_cache_expire_in_seconds,
    )


@lru_cache()
def get_persons_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    return SearchService(
        cache_service=redis,
        elastic=elastic,
        index_name=EsIndexes.persons.value,
        cache_expire=settings.person_cache_expire_in_seconds,
    )
