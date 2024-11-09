import logging
from typing import Dict, List, Optional
from uuid import UUID

from core.services import BaseService
from elasticsearch import exceptions
from models.film import FilmShort
from models.person import Person

logger = logging.getLogger(__name__)


class PersonService(BaseService):
    async def get_all_persons(self) -> List[Person]:
        try:
            response = await self.elastic.search(
                index="persons", body={"query": {"match_all": {}}}
            )
            return [
                Person(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for persons retrieval"
            )
            return []
        except Exception as e:
            logger.exception(f"Error retrieving all persons: {e}")
            return []

    async def get_person_by_id(self, person_id: UUID) -> Optional[Person]:
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

    async def get_person_films(self, person_id: UUID) -> List[FilmShort]:
        query = self._build_person_films_query(person_id)
        try:
            response = await self.elastic.search(
                index="movies", body={"query": query}
            )
            return [
                FilmShort(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
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

    def _build_person_films_query(self, person_id: UUID) -> Dict:
        return {
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
