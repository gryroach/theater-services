from uuid import UUID

from pydantic import BaseModel


class FilmShort(BaseModel):
    id: UUID
    title: str
    imdb_rating: float | None


class Film(FilmShort):
    description: str | None
    genres: list[str] | None
