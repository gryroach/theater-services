from typing import Generic, Protocol, TypeVar
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError

from models import Film, FilmShort, Genre, Person

T = TypeVar("T", bound=FilmShort | Film | Genre | Person)
V = TypeVar("V", bound=FilmShort | Film | Genre | Person)


class BaseRepositoryProtocol(Protocol[T, V]):
    async def get_by_id(self, id_: UUID) -> T | None:
        ...

    async def get_all(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[V]:
        ...


class BaseElasticRepository(Generic[T, V]):
    def __init__(
        self,
        index_name: str,
        elastic: AsyncElasticsearch,
        t_model_class: type[T],
        v_model_class: type[V],
    ):
        self.index_name = index_name
        self.elastic = elastic
        self.t_model_class = t_model_class
        self.v_model_class = v_model_class

    async def get_by_id(self, id_: UUID) -> T | None:
        try:
            doc = await self.elastic.get(index=self.index_name, id=str(id_))
        except NotFoundError:
            return None
        return self.t_model_class(**doc["_source"])

    async def get_all(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[V]:
        query: dict = {"match_all": {}}
        return await self._get_paginated_result(
            query, page_size, page_number, sort
        )

    async def _get_paginated_result(
        self,
        query: dict,
        page_size: int,
        page_number: int,
        sort: str | None = None,
        index_name: str | None = None,
        model: type[V] | None = None,
    ) -> list[V]:
        index_name = index_name or self.index_name
        model = model or self.v_model_class

        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }

        if sort is not None:
            order, row = (
                ("desc", sort[1:]) if sort[0] == "-" else ("asc", sort)
            )
            body["sort"] = [{row: {"order": order}}]

        docs = await self.elastic.search(index=index_name, body=body)
        return [model(**hit["_source"]) for hit in docs["hits"]["hits"]]
