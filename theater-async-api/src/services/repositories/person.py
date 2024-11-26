from typing import Protocol
from uuid import UUID

from db.elastic import EsIndexes
from models import FilmShort, Person
from services.repositories.base_repositories import (
    BaseElasticRepository,
    BaseRepositoryProtocol,
)


class PersonRepositoryProtocol(BaseRepositoryProtocol, Protocol):
    async def get_person_films(
        self,
        person_id: UUID,
        page_size: int,
        page_number: int,
    ) -> list[FilmShort]:
        ...


class PersonElasticRepository(
    BaseElasticRepository[Person, Person | FilmShort]
):
    async def get_person_films(
        self,
        person_id: UUID,
        page_size: int,
        page_number: int,
    ) -> list[FilmShort]:
        query = {
            "bool": {
                "should": [
                    {
                        "nested": {
                            "path": "directors",
                            "query": {"term": {
                                "directors.id": str(person_id)}
                            },
                        }
                    },
                    {
                        "nested": {
                            "path": "writers",
                            "query": {"term": {"writers.id": str(person_id)}},
                        }
                    },
                    {
                        "nested": {
                            "path": "actors",
                            "query": {"term": {"actors.id": str(person_id)}},
                        }
                    },
                ]
            }
        }
        return await self._get_paginated_result(
            query,
            page_size,
            page_number,
            index_name=EsIndexes.movies.value,
            model=FilmShort,
        )
