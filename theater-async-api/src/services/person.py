import logging
from functools import lru_cache
from uuid import UUID

from core.services import BaseService
from db.elastic import get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, exceptions
from elasticsearch_dsl import AsyncSearch, Q
from fastapi import Depends
from models.film import FilmShort
from models.person import Person
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class PersonService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_all_persons(self) -> list[Person]:
        try:
            search = AsyncSearch(using=self.elastic, index="persons").query(
                "match_all"
            )
            response = await search.execute()
            return [Person(**hit.to_dict()) for hit in response]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for persons retrieval"
            )
            return []
        except Exception as e:
            logger.exception(f"Error retrieving all persons: {e}")
            return []

    async def get_person_by_id(self, person_id: UUID) -> Person | None:
        try:
            response = await self.elastic.get(
                index="persons", id=str(person_id)
            )
            return Person(**response["_source"]) if response else None
        except exceptions.NotFoundError:
            logger.warning(f"Person with ID {person_id} not found")
            return None
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for person retrieval"
            )
            return None
        except Exception as e:
            logger.exception(f"Error retrieving person by ID {person_id}: {e}")
            return None

    async def get_person_films(self, person_id: UUID) -> list[FilmShort]:
        search = AsyncSearch(using=self.elastic, index="movies").query(
            "bool",
            should=[
                Q(
                    "nested",
                    path="directors",
                    query=Q("term", directors__id=str(person_id)),
                ),
                Q(
                    "nested",
                    path="writers",
                    query=Q("term", writers__id=str(person_id)),
                ),
                Q(
                    "nested",
                    path="actors",
                    query=Q("term", actors__id=str(person_id)),
                ),
            ],
        )

        try:
            response = await search.execute()
            return [FilmShort(**hit.to_dict()) for hit in response]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for person films retrieval"
            )
            return []
        except Exception as e:
            logger.exception(
                f"Error retrieving films for person {person_id}: {e}"
            )
            return []


@lru_cache()
def get_person_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncSearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
