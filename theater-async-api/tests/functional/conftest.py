import asyncio
import logging
import random
import uuid

import aiohttp
import pytest
import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from redis.asyncio import Redis
from tests.functional.settings import (
    es_genres_settings,
    es_movies_settings,
    es_persons_settings,
    test_settings,
)

# Настройки индексов Elasticsearch
INDEX_SETTINGS_MAP = {
    "movies": es_movies_settings,
    "genres": es_genres_settings,
    "persons": es_persons_settings,
}
STATUSES_WITH_DYNAMIC_BODY = [
    422,
]

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """
    Создает и возвращает event loop для сессии тестов.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client() -> AsyncElasticsearch:
    """
    Создает клиент Elasticsearch для работы с асинхронным API.
    """
    client = AsyncElasticsearch(
        hosts=test_settings.elasticsearch_url, verify_certs=False
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(name="redis_client", scope="session")
async def redis_client() -> Redis:
    """
    Создает асинхронного клиента Redis для использования в тестах.
    """
    client = Redis(
        host=test_settings.redis_host, port=test_settings.redis_port
    )
    yield client
    await client.aclose()


@pytest_asyncio.fixture(name="clear_redis")
def clear_redis(redis_client: Redis):
    """
    Очищает Redis.
    """

    async def inner() -> None:
        await redis_client.flushall()

    return inner


@pytest_asyncio.fixture(name="clear_es_indices")
def clear_es_indices(es_client: AsyncElasticsearch):
    """
    Удаляет указанный индекс в Elasticsearch.
    """

    async def inner(
        index_name: str,
    ) -> None:
        es_settings = INDEX_SETTINGS_MAP[index_name]
        if await es_client.indices.exists(index=es_settings.es_index):
            await es_client.indices.delete(index=es_settings.es_index)

    return inner


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client: AsyncElasticsearch):
    """
    Записывает данные в указанный индекс Elasticsearch.
    """

    async def inner(
        data: list[dict], index_name: str, prepare: bool = True
    ) -> None:
        es_settings = INDEX_SETTINGS_MAP[index_name]
        if await es_client.indices.exists(index=es_settings.es_index):
            await es_client.indices.delete(index=es_settings.es_index)
        await es_client.indices.create(
            index=es_settings.es_index, **es_settings.es_index_mapping
        )
        if prepare:
            data = prepare_data_for_es(data, es_settings.es_index)
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
    """
    Выполняет GET-запрос к тестируемому сервису.
    """

    async def inner(url: str, params: dict = None) -> tuple[int, dict]:
        url = f"{test_settings.service_url}{url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                body = await response.json()
                status = response.status
        return status, body

    return inner


def generate_uuids(seed: int = 42, count: int = 40) -> list[str]:
    """
    Генерирует список UUID с фиксированным seed.

    Args:
        seed (int): Seed для генератора случайных чисел.
        count (int): Количество UUID.

    Returns:
        list[str]: Список UUID.
    """
    random.seed(seed)
    return [str(uuid.UUID(int=random.getrandbits(128))) for _ in range(count)]


UUIDS = generate_uuids()


@pytest.fixture
def es_movies_data() -> list[dict]:
    """
    Возвращает тестовые данные для индекса фильмов Elasticsearch.
    """
    return [
        {
            "id": uuid,
            "imdb_rating": 8.5,
            "genres": ["Action", "Sci-Fi"],
            "genres_details": [
                {
                    "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3100",
                    "name": "Action",
                },
                {
                    "id": "fb111f22-121e-44a7-b78f-b19191810100",
                    "name": "Sci-Fi",
                },
            ],
            "title": "The Star",
            "description": "New World",
            "actors_names": ["Ann", "Bob"],
            "directors_names": ["Stan"],
            "writers_names": ["Ben", "Howard"],
            "actors": [
                {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "name": "Ann"},
                {"id": "fb111f22-121e-44a7-b78f-b19191810fbf", "name": "Bob"},
            ],
            "writers": [
                {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5", "name": "Ben"},
                {
                    "id": "b45bd7bc-2e16-46d5-b125-983d356768c6",
                    "name": "Howard",
                },
            ],
            "directors": [
                {"id": "4c1d0404-075e-4027-b4ae-01d5d4a10a9b", "name": "Stan"}
            ],
        }
        for uuid in UUIDS
    ]


@pytest.fixture
def es_persons_data() -> list[dict]:
    """
    Возвращает тестовые данные для индекса персон Elasticsearch.
    """
    uuid = UUIDS[0]
    return [
        {
            "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95",
            "full_name": "Ann",
            "films": [
                {
                    "id": uuid,
                    "title": "The Star",
                    "imdb_rating": 8.5,
                    "roles": ["actor"],
                }
            ],
        },
        {
            "id": "fb111f22-121e-44a7-b78f-b19191810fbf",
            "full_name": "Bob",
            "films": [
                {
                    "id": uuid,
                    "title": "The Star",
                    "imdb_rating": 8.5,
                    "roles": ["actor"],
                }
            ],
        },
        {
            "id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5",
            "full_name": "Ben",
            "films": [
                {
                    "id": uuid,
                    "title": "The Star",
                    "imdb_rating": 8.5,
                    "roles": ["writer"],
                }
            ],
        },
        {
            "id": "b45bd7bc-2e16-46d5-b125-983d356768c6",
            "full_name": "Howard",
            "films": [
                {
                    "id": uuid,
                    "title": "The Star",
                    "imdb_rating": 8.5,
                    "roles": ["writer"],
                }
            ],
        },
        {
            "id": "4c1d0404-075e-4027-b4ae-01d5d4a10a9b",
            "full_name": "Stan",
            "films": [
                {
                    "id": uuid,
                    "title": "The Star",
                    "imdb_rating": 8.5,
                    "roles": ["director"],
                }
            ],
        },
    ]


@pytest.fixture
def es_genres_data() -> list[dict]:
    """
    Возвращает тестовые данные для индекса жанров Elasticsearch.
    """
    return [
        {
            "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3100",
            "name": "Action",
            "description": "About Action",
        },
        {
            "id": "fb111f22-121e-44a7-b78f-b19191810100",
            "name": "Sci-Fi",
            "description": "About Sci-Fi",
        },
    ]

@pytest.fixture
def film_id() -> str:
    return UUIDS[0]



def prepare_data_for_es(in_data: list[dict], index_name: str) -> list[dict]:
    """
    Преобразует данные для загрузки в Elasticsearch.

    Args:
        in_data (list[dict]): Исходные данные.
        index_name (str): Имя индекса.

    Returns:
        list[dict]: Преобразованные данные.
    """
    return [
        {"_index": index_name, "_id": row["id"], "_source": row}
        for row in in_data
    ]
