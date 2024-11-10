from pydantic import BaseModel


class FilmShort(BaseModel):
    id: str
    title: str
    imdb_rating: float | None

class Film(FilmShort):
    description: str | None
    genres: list[str] | None
