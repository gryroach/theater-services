from dataclasses import dataclass
from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from pydantic import BaseModel
from redis.asyncio import Redis

from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from models import FilmShort, Genre, Person
from models.common import SearchResponse
from services.base import BaseEsService


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


class SearchService(BaseEsService):
    async def search(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse:
        result = await self.get_data_from_cache(
            True,
            query_string=query_string,
            page_size=page_size,
            page_number=page_number,
        )
        if not result:
            result = await self._get_search_result(
                query_string=query_string, page_size=page_size, page_number=page_number
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
    ):
        fields = INDEX_SEARCH_FIELDS[self.index_name].search_fields
        response_type = INDEX_SEARCH_FIELDS[self.index_name].response_type
        query = {"multi_match": {"query": query_string, "fields": fields}}
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        es_result = await self.elastic.search(index=self.index_name, body=body)
        return SearchResponse(
            count=es_result["hits"]["total"]["value"],
            result=[
                response_type(**hit["_source"]) for hit in es_result["hits"]["hits"]
            ],
        )


@lru_cache()
def get_films_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
    index_name: str = EsIndexes.movies.value,
    model: type[BaseModel] = SearchResponse,
    cache_expire: int = 60,
) -> SearchService:
    return SearchService(
        redis, elastic, index_name, model, cache_expire
    )


@lru_cache()
def get_genres_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
    index_name: str = EsIndexes.genres.value,
    model: type[BaseModel] = SearchResponse,
    cache_expire: int = 60,
) -> SearchService:
    return SearchService(redis, elastic, index_name, model, cache_expire)


@lru_cache()
def get_persons_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
    index_name: str = EsIndexes.persons.value,
    model: type[BaseModel] = SearchResponse,
    cache_expire: int = 60,
) -> SearchService:
    return SearchService(redis, elastic, index_name, model, cache_expire)
