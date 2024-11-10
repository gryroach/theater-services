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
from models.genre import Genre
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class GenreService(BaseService):
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_all_genres(self) -> list[Genre]:
        try:
            search = AsyncSearch(using=self.elastic, index="genres").query(
                "match_all"
            )
            response = await search.execute()
            return [Genre(**hit.to_dict()) for hit in response]
        except exceptions.ConnectionError:
            logger.error(
                "Failed to connect to Elasticsearch for genres retrieval"
            )
            return []
        except Exception as e:
            logger.exception(f"Error retrieving all genres: {e}")
            return []

    async def get_genre_by_id(self, genre_id: UUID) -> Genre | None:
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
    ) -> list[FilmShort]:
        search = (
            AsyncSearch(using=self.elastic, index="movies")
            .query(
                "nested",
                path="genres_details",
                query=Q("term", genres_details__id=str(genre_id)),
            )
            .sort("-imdb_rating")[
                page_size * (page_number - 1) : page_size * page_number
            ]
        )

        try:
            response = await search.execute()
            return [FilmShort(**hit.to_dict()) for hit in response]
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


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncSearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
