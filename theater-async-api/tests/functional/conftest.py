import asyncio
import logging
import random
import uuid
from http import HTTPStatus

import pytest


STATUSES_WITH_DYNAMIC_BODY = [
    HTTPStatus.UNPROCESSABLE_ENTITY,
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


def generate_ratings_for_films(uuids: list[str]) -> dict[str, float]:
    """
    Генерирует рейтинг для каждого фильма по его UUID.

    Args:
        uuids (list[str]): Список UUID.

    Returns:
        dict[str, float]: Словарь, где ключами являются UUID фильмов,
        а значениями — случайно сгенерированные рейтинги
        в диапазоне от 1.0 до 10.0 с шагом 0.1.
    """
    return {uuid: random.randint(10, 100) / 10 for uuid in uuids}


UUIDS = generate_uuids()
MOVIES_RATINGS = generate_ratings_for_films(uuids=UUIDS)


@pytest.fixture
def es_movies_data() -> list[dict]:
    """
    Возвращает тестовые данные для индекса фильмов Elasticsearch.
    """
    return [
        {
            "id": uuid,
            "imdb_rating": rating,
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
        for uuid, rating in MOVIES_RATINGS.items()
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


@pytest.fixture
def imdb_rating():
    def inner(movie_id: str):
        return MOVIES_RATINGS[movie_id]

    return inner


@pytest.fixture
def expected_body():
    sorted_movies = sorted(
        MOVIES_RATINGS.items(), key=lambda x: x[1], reverse=True
    )
    return [
        {
            'id': movie_id,
            'title': 'The Star',
            'imdb_rating': rating
        }
        for movie_id, rating in sorted_movies
    ]


@pytest.fixture
def search_expected_body():
    result = [
        {
            'id': movie_id,
            'title': 'The Star',
            'imdb_rating': rating
        }
        for movie_id, rating in MOVIES_RATINGS.items()
    ]
    count = len(MOVIES_RATINGS)
    return {"count": count, "result": result[:10]}
