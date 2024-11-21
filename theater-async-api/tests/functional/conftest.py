import asyncio
import uuid

import aiohttp
import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from tests.functional.settings import (
    es_genres_settings, es_movies_settings,
    es_persons_settings, test_settings,
)

INDEX_SETTINGS_MAP = {
    "movies": es_movies_settings,
    "genres": es_genres_settings,
    "persons": es_persons_settings,
}


@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client():
    es_client = AsyncElasticsearch(
        hosts=test_settings.elasticsearch_url, verify_certs=False
    )
    yield es_client
    await es_client.close()


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client: AsyncElasticsearch):
    async def inner(data: list[dict], index_name: str, prepare: bool = True):
        es_settings = INDEX_SETTINGS_MAP[index_name]

        if await es_client.indices.exists(index=es_settings.es_index):
            await es_client.indices.delete(index=es_settings.es_index)
        await es_client.indices.create(
            index=es_settings.es_index, **es_settings.es_index_mapping
        )

        if prepare:
            data = prepare_data_for_es(data, index_name)
        updated, errors = await async_bulk(
            client=es_client,
            actions=data,
            refresh=True,
        )

        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner


@pytest_asyncio.fixture(name="make_get_request")
def make_get_request():
    async def inner(url: str, params: dict) -> tuple[int, dict]:
        url = test_settings.service_url + url
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                body = await response.json()
                status = response.status
        return status, body

    return inner


@pytest.fixture
def es_movies_data():
    return [
        {
            "id": str(uuid.uuid4()),
            "imdb_rating": 8.5,
            "genres": ["Action", "Sci-Fi"],
            "title": "The Star",
            "description": "New World",
            "actors_names": ["Ann", "Bob"],
            "directors_names": ["Stan"],
            "writers_names": ["Ben", "Howard"],
            "actors": [
                {
                    "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95",
                    "name": "Ann",
                },
                {
                    "id": "fb111f22-121e-44a7-b78f-b19191810fbf",
                    "name": "Bob",
                },
            ],
            "writers": [
                {
                    "id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5",
                    "name": "Ben",
                },
                {
                    "id": "b45bd7bc-2e16-46d5-b125-983d356768c6",
                    "name": "Howard",
                },
            ],
        }
        for _ in range(60)
    ]


def prepare_data_for_es(in_data: list[dict], index_name: str) -> list[dict]:
    prepared_data: list[dict] = []
    for row in in_data:
        data = {"_index": index_name, "_id": row["id"]}
        data.update({"_source": row})
        prepared_data.append(data)
    return prepared_data
