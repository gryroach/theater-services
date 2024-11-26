from typing import Protocol
from uuid import UUID

from db.elastic import EsIndexes
from models import FilmShort, Genre
from services.repositories.base_repositories import (
    BaseElasticRepository,
    BaseRepositoryProtocol,
)


class GenreRepositoryProtocol(BaseRepositoryProtocol, Protocol):
    async def get_popular_films(
        self,
        genre_id: UUID,
        page_size: int,
        page_number: int,
    ) -> list[FilmShort]:
        ...


class GenreElasticRepository(BaseElasticRepository[Genre, Genre | FilmShort]):
    async def get_popular_films(
        self,
        genre_id: UUID,
        page_size: int,
        page_number: int,
    ) -> list[FilmShort]:
        sort = "-imdb_rating"
        query = {
            "nested": {
                "path": "genres_details",
                "query": {"term": {"genres_details.id": str(genre_id)}},
            }
        }
        return await self._get_paginated_result(
            query,
            page_size,
            page_number,
            sort,
            EsIndexes.movies.value,
            FilmShort,
        )
