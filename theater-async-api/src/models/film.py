from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class Film(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None


class FilmShort(BaseModel):
    id: UUID
    title: str
    imdb_rating: float
