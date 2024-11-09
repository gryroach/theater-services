from pydantic import BaseModel


class FilmToList(BaseModel):
    id: str
    title: str
    imdb_rating: float | None

class Film(FilmToList):
    description: str | None
    genres: list[str] | None
