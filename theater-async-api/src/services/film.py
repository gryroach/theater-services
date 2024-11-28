from uuid import UUID

from models.enums import FilmsSortOptions
from models.film import Film, FilmShort
from services.base import BaseService


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
