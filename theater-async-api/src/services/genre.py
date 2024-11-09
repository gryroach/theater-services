import logging
from typing import Dict, List, Optional
from uuid import UUID

from core.services import BaseService
from elasticsearch import exceptions
from models.film import FilmShort
from models.genre import Genre

logger = logging.getLogger(__name__)


class GenreService(BaseService):
    async def get_all_genres(self) -> List[Genre]:
        try:
            response = await self.elastic.search(
                index="genres", body={"query": {"match_all": {}}}
            )
            return [
                Genre(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for genres retrieval"
            )
            return []
        except Exception as e:
            logger.exception(f"Error retrieving all genres: {e}")
            return []

    async def get_genre_by_id(self, genre_id: UUID) -> Optional[Genre]:
        try:
            response = await self.elastic.get(index="genres", id=str(genre_id))
            return Genre(**response["_source"]) if response else None
        except exceptions.NotFoundError:
            logger.warning(f"Genre with ID {genre_id} not found")
            return None
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for genre retrieval"
            )
            return None
        except Exception as e:
            logger.exception(f"Error retrieving genre by ID {genre_id}: {e}")
            return None

    async def get_popular_films(
        self, genre_id: UUID, page_size: int, page_number: int
    ) -> List[FilmShort]:
        search_query = self._build_popular_films_query(
            genre_id, page_size, page_number
        )
        try:
            response = await self.elastic.search(
                index="movies", body=search_query
            )
            return [
                FilmShort(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for popular films retrieval"
            )
            return []
        except Exception as e:
            logger.exception(
                f"Error retrieving popular films for genre {genre_id}: {e}"
            )
            return []

    def _build_popular_films_query(
        self, genre_id: UUID, page_size: int, page_number: int
    ) -> Dict:
        return {
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "query": {
                "nested": {
                    "path": "genres_details",
                    "query": {"term": {"genres_details.id": str(genre_id)}},
                }
            },
            "sort": [{"imdb_rating": "desc"}],
        }
