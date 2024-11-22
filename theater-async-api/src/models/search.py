from pydantic import BaseModel
from typing import TypeVar, Generic, List

from models import FilmShort, Genre, Person

T = TypeVar("T")


class SearchResponse(BaseModel, Generic[T]):
    count: int
    result: List[T]


class FilmSearch(SearchResponse[FilmShort]):
    pass


class PersonSearch(SearchResponse[Person]):
    pass


class GenreSearch(SearchResponse[Genre]):
    pass
