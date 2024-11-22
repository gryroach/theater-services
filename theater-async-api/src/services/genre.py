import logging
from functools import lru_cache
from uuid import UUID

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from models import FilmShort
from models.genre import Genre
from redis.asyncio import Redis
from services.base import BaseService

logger = logging.getLogger(__name__)


class GenreService(BaseService):
    async def get_all_genres(self, page_size: int, page_number: int) -> list[Genre]:
        genres = await self.get_data_from_cache(
            Genre, page_size=page_size, page_number=page_number
        )
        if not genres:
            genres = await self._get_all_genres_from_elastic(page_size, page_number)
            if genres:
                await self.put_into_cache(
                    genres, page_size=page_size, page_number=page_number
                )
        return genres

    async def get_genre_by_id(self, genre_id: UUID) -> Genre | None:
        genre = await self.get_data_from_cache(Genre, single=True, id=genre_id)
        if not genre:
            genre = await self._get_genre_by_id_from_elastic(genre_id)
            if genre is not None:
                await self.put_into_cache(genre, id=genre_id)
        return genre

    async def get_popular_films(
        self, genre_id: UUID, page_size: int, page_number: int
    ) -> list[FilmShort]:
        films = await self.get_data_from_cache(
            FilmShort,
            id=genre_id,
            page_size=page_size,
            page_number=page_number,
        )
        if not films:
            films = await self._get_popular_films_from_elastic(
                genre_id, page_size, page_number
            )
            if films:
                await self.put_into_cache(
                    films,
                    id=genre_id,
                    page_size=page_size,
                    page_number=page_number,
                )
        return films

    async def _get_all_genres_from_elastic(
        self, page_size: int, page_number: int
    ) -> list[Genre]:
        body = {
            "query": {"match_all": {}},
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        try:
            es_result = await self.elastic.search(index=self.index_name, body=body)
            return [Genre(**hit["_source"]) for hit in es_result["hits"]["hits"]]
        except Exception as e:
            logger.exception(f"Error retrieving all genres: {e}")
            return []

    async def _get_genre_by_id_from_elastic(self, genre_id: UUID) -> Genre | None:
        try:
            es_result = await self.elastic.get(index=self.index_name, id=str(genre_id))
            return Genre(**es_result["_source"]) if es_result else None
        except NotFoundError:
            logger.warning(f"Genre with ID {genre_id} not found")
            return None
        except Exception as e:
            logger.exception(f"Error retrieving genre by ID {genre_id}: {e}")
            return None

    async def _get_popular_films_from_elastic(
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
            response = await self.elastic.search(
                index=EsIndexes.movies.value, body=body
            )
            return [FilmShort(**hit["_source"]) for hit in response["hits"]["hits"]]
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
    return GenreService(
        cache_service=redis,
        elastic=elastic,
        index_name=EsIndexes.genres.value,
        cache_expire=settings.person_cache_expire_in_seconds,
    )
