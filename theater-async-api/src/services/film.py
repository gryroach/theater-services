from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from core.config import settings
from db.elastic import EsIndexes, get_elastic
from db.redis import get_redis
from models.enums import FilmsSortOptions
from models.film import Film, FilmShort
from models.genre import Genre
from services.base import BaseCacheService


class FilmService(BaseCacheService):
    async def get_film_by_id(self, film_id: str) -> Film | None:
        film = await self.get_data_from_cache(Film, single=True, id=film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
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
            FilmShort, sort=sort, page_size=page_size, page_number=page_number, genre=genre
        )
        if not films:
            films = await self._get_films_from_elastic(
                sort, page_size, page_number, genre
            )
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

    async def _get_film_from_elastic(self, film_id: str) -> Film | None:
        try:
            doc = await self.elastic.get(index=self.index_name, id=film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def _get_genre_from_elastic(self, genre: str | UUID):
        try:
            doc = await self.elastic.get(index=EsIndexes.genres.value, id=genre)
        except NotFoundError:
            return None
        return Genre(**doc["_source"])

    async def _get_films_from_elastic(
        self,
        sort: FilmsSortOptions,
        page_size: int,
        page_number: int,
        genre: UUID | None,
    ) -> list[FilmShort] | None:
        query = {"match_all": {}}

        if genre:
            if genre_record := await self._get_genre_from_elastic(genre):
                query = {"bool": {"filter": [{"term": {"genres": genre_record.name}}]}}

        order, row = ("desc", sort[1:]) if sort[0] == "-" else ("asc", sort)
        sort = [{row: {"order": order}}]
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "sort": sort,
        }
        docs = await self.elastic.search(index=self.index_name, body=body)
        return [FilmShort(**hit["_source"]) for hit in docs["hits"]["hits"]]


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(
        redis,
        elastic,
        EsIndexes.movies.value,
        settings.film_cache_expire_in_seconds,
    )
