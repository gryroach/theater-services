from functools import lru_cache
from uuid import UUID

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends
from models.enums import FilmsSortOptions
from models.film import Film, FilmShort
from redis.asyncio import Redis
from services.base import BaseService
from services.repositories.film import FilmElasticRepository


class FilmService(BaseService):
    async def get_film_by_id(self, film_id: UUID) -> Film | None:
        film = await self.get_data_from_cache(Film, True, id=film_id)
        if not film:
            film = await self.repository.get_by_id(film_id)
            if film is not None:
                await self.put_into_cache(film, id=film_id)
        return film

    async def get_films(
        self,
        sort: FilmsSortOptions,
        page_size: int,
        page_number: int,
        genre: UUID | None,
    ) -> list[FilmShort]:
        films = await self.get_data_from_cache(
            FilmShort,
            sort=sort,
            page_size=page_size,
            page_number=page_number,
            genre=genre,
        )
        if films:
            return films

        if genre:
            films = await self.repository.get_by_genre(
                page_size, page_number, sort, genre
            )
        else:
            films = await self.repository.get_all(page_size, page_number, sort)

        if not films:
            return []
        await self.put_into_cache(
            films,
            sort=sort,
            page_size=page_size,
            page_number=page_number,
            genre=genre,
        )
        return films


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    repository = FilmElasticRepository(
        EsIndexes.movies.value, elastic, Film, FilmShort
    )
    return FilmService(
        repository=repository,
        cache_service=redis,
        key_prefix=repository.index_name,
        cache_expire=settings.film_cache_expire_in_seconds,
    )
