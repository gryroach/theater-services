from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class FilmRole(BaseModel):
    id: UUID
    title: str


class Person(BaseModel):
    id: UUID
    full_name: str
    roles: List[str]
    films: List[FilmRole]
