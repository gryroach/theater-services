import logging
from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import FilmShort
from models.person import Person

logger = logging.getLogger(__name__)


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_all_persons(
        self, page_size: int, page_number: int
    ) -> list[Person]:
        body = {
            "query": {"match_all": {}},
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        try:
            response = await self.elastic.search(index="persons", body=body)
            return [
                Person(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.exception(f"Error retrieving all persons: {e}")
            return []

    async def get_person_by_id(self, person_id: UUID) -> Person | None:
        try:
            response = await self.elastic.get(
                index="persons", id=str(person_id)
            )
            return Person(**response["_source"]) if response else None
        except NotFoundError:
            logger.warning(f"Person with ID {person_id} not found")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving person by ID {person_id}: {e}")
            return None

    async def get_person_films(
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
            response = await self.elastic.search(index="movies", body=body)
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
    return PersonService(redis, elastic)
