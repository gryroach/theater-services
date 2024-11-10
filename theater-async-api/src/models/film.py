from pydantic import BaseModel


<<<<<<< HEAD
class FilmShort(BaseModel):
    id: str
    title: str
    imdb_rating: float | None

class Film(FilmShort):
    description: str | None
    genres: list[str] | None
=======
class Film(BaseModel):
    id: str
    title: str
    description: str
>>>>>>> main
