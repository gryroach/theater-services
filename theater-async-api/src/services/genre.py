import logging
from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import FilmShort
from models.genre import Genre

logger = logging.getLogger(__name__)


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_all_genres(
        self, page_size: int, page_number: int
    ) -> list[Genre]:
        body = {
            "query": {"match_all": {}},
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        try:
            response = await self.elastic.search(index="genres", body=body)
            return [
                Genre(**hit["_source"]) for hit in response["hits"]["hits"]
            ]
        except Exception as e:
            logger.exception(f"Error retrieving all genres: {e}")
            return []

    async def get_genre_by_id(self, genre_id: UUID) -> Genre | None:
        try:
            response = await self.elastic.get(index="genres", id=str(genre_id))
            return Genre(**response["_source"]) if response else None
        except NotFoundError:
            logger.warning(f"Genre with ID {genre_id} not found")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving genre by ID {genre_id}: {e}")
            return None

    async def get_popular_films(
        self, genre_id: UUID, page_size: int, page_number: int
    ) -> list[FilmShort]:
        body = {
            "query": {
                "nested": {
                    "path": "genres_details",
                    "query": {"term": {"genres_details.id": str(genre_id)}},
                }
            },
            "sort": [{"imdb_rating": {"order": "desc"}}],
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
                f"Error retrieving popular films for genre {genre_id}: {e}"
            )
            return []


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
