from enum import Enum
from typing import Optional

from elasticsearch import AsyncElasticsearch


class EsIndexes(Enum):
    movies: str = "movies"
    genres: str = "genres"
    persons: str = "persons"


es: Optional[AsyncElasticsearch] = None


async def get_elastic() -> AsyncElasticsearch:
    return es
