import logging
from uuid import UUID

from models import FilmShort
from models.genre import Genre
from services.base import BaseService

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
