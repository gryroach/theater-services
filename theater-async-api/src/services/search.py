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


class SearchService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def search(
        self,
        index: str,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse:
        fields = INDEX_SEARCH_FIELDS[index].search_fields
        response_type = INDEX_SEARCH_FIELDS[index].response_type
        query = {"multi_match": {"query": query_string, "fields": fields}}
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        result = await self.elastic.search(index=index, body=body)
        return SearchResponse(
            count=result["hits"]["total"]["value"],
            result=[response_type(**hit["_source"]) for hit in result["hits"]["hits"]],
        )


@lru_cache()
def get_search_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    return SearchService(redis, elastic)
