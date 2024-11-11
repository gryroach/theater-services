import json
from functools import lru_cache
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from db.elastic import get_elastic
from db.redis import get_redis
from models.enums import FilmsSortOptions
from models.film import Film
from models.genre import Genre

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Film | None:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)

        return film

    async def get_films(
        self,
        sort: FilmsSortOptions,
        page_size: int,
        page_number: int,
        genre: UUID | None,
    ) -> list[Film]:
        films = await self._films_from_cache(
            sort, page_size, page_number, genre
        )
        if not films:
            films = await self._get_films_from_elastic(
                sort, page_size, page_number, genre
            )
        await self._put_films_to_cache(
            sort, page_size, page_number, genre, films
        )
        return films

    async def _get_film_from_elastic(self, film_id: str) -> list[Film] | None:
        try:
            doc = await self.elastic.get(index="movies", id=film_id)
        except NotFoundError:
            return None
        return Film(**doc["_source"])

    async def _get_genre_from_elastic(self, genre: str | UUID):
        try:
            doc = await self.elastic.get(index="genres", id=genre)
        except NotFoundError:
            return None
        return Genre(**doc["_source"])

    async def _get_films_from_elastic(
        self,
        sort: FilmsSortOptions,
        page_size: int,
        page_number: int,
        genre: UUID | None,
    ) -> list[Film] | None:
        query = {"match_all": {}}

        if genre:
            if genre_record := await self._get_genre_from_elastic(genre):
                query = {
                    "bool": {
                        "filter": [{"term": {"genres": genre_record.name}}]
                    }
                }

        order, row = ("desc", sort[1:]) if sort[0] == "-" else ("asc", sort)
        sort = [{row: {"order": order}}]
        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
            "sort": sort,
        }
        docs = await self.elastic.search(index="movies", body=body)
        return [Film(**hit["_source"]) for hit in docs["hits"]["hits"]]

    async def _film_from_cache(self, film_id: str) -> Film | None:
        data = await self.redis.get(film_id)
        if not data:
            return None

        film = Film.model_validate_json(data)
        return film

    async def _films_from_cache(
        self,
        sort: str,
        page_size: int,
        page_number: int,
        genre: UUID,
    ) -> list[Film] | None:
        key = self._generate_key(sort, page_size, page_number, genre)

        data = await self.redis.get(key)
        if not data:
            return None

        film_list = json.loads(data)
        films = [Film.model_validate_json(film) for film in film_list]
        return films

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(
            film.id, film.model_dump_json(), FILM_CACHE_EXPIRE_IN_SECONDS
        )

    async def _put_films_to_cache(
        self,
        sort: str,
        page_size: int,
        page_number: int,
        genre: UUID | None,
        films: list[Film],
    ) -> None:
        key = self._generate_key(sort, page_size, page_number, genre)
        films_list = json.dumps([film.model_dump_json() for film in films])
        await self.redis.set(key, films_list, FILM_CACHE_EXPIRE_IN_SECONDS)

    @staticmethod
    def _generate_key(
        sort: str, page_size: int, page_number: int, genre: UUID | None
    ) -> str:
        return f"movies_{sort}_{page_size}_{page_number}_{genre}"


@lru_cache()
def get_film_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
