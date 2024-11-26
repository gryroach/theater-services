from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from db.elastic import EsIndexes
from elasticsearch import AsyncElasticsearch
from models import FilmShort, Genre, Person
from models.search import SearchResponse
from pydantic import BaseModel

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


class SearchRepositoryProtocol(Protocol[T]):
    async def get_search_result(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse[T]:
        ...


class SearchElasticRepository(Generic[T]):
    def __init__(
        self,
        index_name: str,
        elastic: AsyncElasticsearch,
    ):
        self.index_name = index_name
        self.elastic = elastic

    async def get_search_result(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse[T]:
        fields = INDEX_SEARCH_FIELDS[self.index_name].search_fields
        response_type = INDEX_SEARCH_FIELDS[self.index_name].response_type

        query = {"multi_match": {"query": query_string, "fields": fields}}
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        es_result = await self.elastic.search(index=self.index_name, body=body)
        return SearchResponse[T](
            count=es_result["hits"]["total"]["value"],
            result=[
                response_type(**hit["_source"])
                for hit in es_result["hits"]["hits"]
            ],
        )
