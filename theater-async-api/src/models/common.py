from pydantic import BaseModel

from models import FilmShort, Genre, Person


class SearchResponse(BaseModel):
    count: int
    result: list[FilmShort | Person | Genre]
