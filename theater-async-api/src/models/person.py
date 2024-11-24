from uuid import UUID

from pydantic import BaseModel


class FilmRole(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
    roles: list[str]


class Person(BaseModel):
    id: UUID
    full_name: str
    films: list[FilmRole] | None = None
