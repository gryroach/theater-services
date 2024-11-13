from enum import Enum

from elasticsearch import AsyncElasticsearch


class EsIndexes(Enum):
    movies = "movies"
    genres = "genres"
    persons = "persons"


es: AsyncElasticsearch | None = None


async def get_elastic() -> AsyncElasticsearch:
    return es
