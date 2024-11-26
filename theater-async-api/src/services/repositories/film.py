from typing import Protocol
from uuid import UUID

from db.elastic import EsIndexes
from elasticsearch import NotFoundError
from models import Film, FilmShort, Genre
from services.repositories.base_repositories import (
    BaseElasticRepository,
    BaseRepositoryProtocol,
)


class FilmRepositoryProtocol(BaseRepositoryProtocol, Protocol):
    async def get_by_genre(
        self,
        page_size: int,
        page_number: int,
        sort: str,
        genre_id: UUID,
    ) -> list[FilmShort]:
        ...


class FilmElasticRepository(BaseElasticRepository[Film, FilmShort]):
    async def get_all(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[FilmShort]:
        query: dict = {"match_all": {}}
        return await self._get_paginated_result(
            query, page_size, page_number, sort
        )

    async def get_by_genre(
        self,
        page_size: int,
        page_number: int,
        sort: str,
        genre_id: UUID,
    ) -> list[FilmShort]:
        if genre_record := await self._get_genre(genre_id):
            query = {
                "bool": {
                    "filter": [
                        {"term": {"genres": genre_record.name}},
                    ]
                }
            }
            return await self._get_paginated_result(
                query, page_size, page_number, sort
            )
        return []

    async def _get_genre(self, genre_id: str | UUID) -> Genre | None:
        try:
            doc = await self.elastic.get(
                index=EsIndexes.genres.value,
                id=genre_id,
            )
        except NotFoundError:
            return None
        return Genre(**doc["_source"])
