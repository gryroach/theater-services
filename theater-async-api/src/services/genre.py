import logging
from functools import lru_cache
from uuid import UUID

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models import FilmShort
from models.genre import Genre
from redis.asyncio import Redis
from services.base import BaseService
from services.repositories.genre import GenreElasticRepository

logger = logging.getLogger(__name__)


class GenreService(BaseService):
    async def get_all_genres(
            self, page_size: int, page_number: int
    ) -> list[Genre]:
        genres = await self.get_data_from_cache(
            Genre, page_size=page_size, page_number=page_number
        )
        if not genres:
            genres = await self.repository.get_all(page_size, page_number)
            if genres:
                await self.put_into_cache(
                    genres, page_size=page_size, page_number=page_number
                )
        return genres

    async def get_genre_by_id(self, genre_id: UUID) -> Genre | None:
        genre = await self.get_data_from_cache(Genre, True, id=genre_id)
        if not genre:
            genre = await self.repository.get_by_id(genre_id)
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
            films = await self.repository.get_popular_films(
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


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    repository = GenreElasticRepository(
        EsIndexes.genres.value, elastic, Genre, Genre
    )
    return GenreService(
        repository=repository,
        cache_service=redis,
        key_prefix=repository.index_name,
        cache_expire=settings.person_cache_expire_in_seconds,
    )
