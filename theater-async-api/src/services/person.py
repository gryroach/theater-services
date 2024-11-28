from uuid import UUID

from models.film import FilmShort
from models.person import Person
from services.base import BaseService


class PersonService(BaseService):
    async def get_all_persons(
            self, page_size: int, page_number: int
    ) -> list[Person]:
        persons = await self.get_data_from_cache(
            Person, page_size=page_size, page_number=page_number
        )
        if not persons:
            persons = await self.repository.get_all(page_size, page_number)
            if persons:
                await self.put_into_cache(
                    persons, page_size=page_size, page_number=page_number
                )
        return persons

    async def get_person_by_id(self, person_id: UUID) -> Person | None:
        person = await self.get_data_from_cache(
            Person, True, id=person_id
        )
        if not person:
            person = await self.repository.get_by_id(person_id)
            if person is not None:
                await self.put_into_cache(person, id=person_id)
        return person

    async def get_person_films(
        self, person_id: UUID, page_size: int, page_number: int
    ) -> list[FilmShort]:
        films = await self.get_data_from_cache(
            FilmShort,
            id=person_id,
            page_size=page_size,
            page_number=page_number,
        )
        if not films:
            films = await self.repository.get_person_films(
                person_id, page_size, page_number
            )
            if films:
                await self.put_into_cache(
                    films,
                    id=person_id,
                    page_size=page_size,
                    page_number=page_number,
                )
        return films
