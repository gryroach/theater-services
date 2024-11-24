import logging
from functools import lru_cache
from uuid import UUID

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models.film import FilmShort
from models.person import Person
from redis.asyncio import Redis
from services.base import BaseService

logger = logging.getLogger(__name__)


class PersonService(BaseService):
    async def get_all_persons(
        self, page_size: int, page_number: int
    ) -> list[Person]:
        persons = await self.get_data_from_cache(
            Person, page_size=page_size, page_number=page_number
        )
        if not persons:
            persons = await self._get_all_persons_from_elastic(
                page_size, page_number
            )
            if persons:
                await self.put_into_cache(
                    persons, page_size=page_size, page_number=page_number
                )
        return persons

    async def get_person_by_id(self, person_id: UUID) -> Person | None:
        person = await self.get_data_from_cache(
            Person, single=True, id=person_id
        )
        if not person:
            person = await self._get_person_by_id_from_elastic(person_id)
            if person is not None:
                await self.put_into_cache(person, id=person_id)
        return person

    async def get_person_films(
        self, person_id: UUID, page_size: int, page_number: int
    ) -> list[FilmShort]:
        films = await self.get_data_from_cache(
            FilmShort,
            id=person_id,
            page_size=page_size,
            page_number=page_number,
        )
        if not films:
            films = await self._get_person_films_from_elastic(
                person_id, page_size, page_number
            )
            if films:
                await self.put_into_cache(
                    films,
                    id=person_id,
                    page_size=page_size,
                    page_number=page_number,
                )
        return films

    async def _get_all_persons_from_elastic(
        self, page_size: int, page_number: int
    ) -> list[Person]:
        query = {"match_all": {}}
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        try:
            response = await self.elastic.search(
                index=EsIndexes.persons.value, body=body
            )
            return [
                Person(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.exception(f"Error retrieving all persons: {e}")
            return []

    async def _get_person_by_id_from_elastic(
        self, person_id: UUID
    ) -> Person | None:
        try:
            response = await self.elastic.get(
                index=EsIndexes.persons.value, id=str(person_id)
            )
            return Person(**response["_source"]) if response else None
        except NotFoundError:
            logger.warning(f"Person with ID {person_id} not found")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving person by ID {person_id}: {e}")
            return None

    async def _get_person_films_from_elastic(
        self, person_id: UUID, page_size: int, page_number: int
    ) -> list[FilmShort]:
        body = {
            "query": {
                "bool": {
                    "should": [
                        {
                            "nested": {
                                "path": "directors",
                                "query": {
                                    "term": {"directors.id": str(person_id)}
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "writers",
                                "query": {
                                    "term": {"writers.id": str(person_id)}
                                },
                            }
                        },
                        {
                            "nested": {
                                "path": "actors",
                                "query": {
                                    "term": {"actors.id": str(person_id)}
                                },
                            }
                        },
                    ]
                }
            },
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        try:
            response = await self.elastic.search(
                index=EsIndexes.movies.value, body=body
            )
            return [
                FilmShort(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.exception(
                f"Error retrieving films for person {person_id}: {e}"
            )
            return []


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(
        cache_service=redis,
        elastic=elastic,
        index_name=EsIndexes.persons.value,
        cache_expire=settings.genre_cache_expire_in_seconds,
    )
