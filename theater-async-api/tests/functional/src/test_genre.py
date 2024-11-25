import logging
from typing import Any

import pytest
from tests.functional.conftest import UUIDS
from tests.functional.settings import es_genres_settings, es_movies_settings
from tests.functional.utils.checks import fetch_and_check_response
from tests.functional.utils.es_helpers import write_data_to_es

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        ("/api/v1/genres/invalid_uuid", {}, 422, {"detail": "Invalid UUID"}),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_genre_uuid(
    es_write_data: Any,
    es_genres_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: dict,
) -> None:
    """
    Тестирует обработку некорректного UUID жанра.
    """
    await write_data_to_es(es_write_data, es_genres_data, es_genres_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/genres/ef86b8ff-3c82-4d31-ad8e-72b69f4e3100",
            {},
            200,
            {
                "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3100",
                "name": "Action",
                "description": "About Action",
            },
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_valid_genre_uuid(
    es_write_data: Any,
    es_genres_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: dict,
) -> None:
    """
    Тестирует обработку корректного UUID жанра.
    """
    await write_data_to_es(es_write_data, es_genres_data, es_genres_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/genres/",
            {"page_size": 2, "page_number": 1},
            200,
            [
                {
                    "id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3100",
                    "name": "Action",
                },
                {
                    "id": "fb111f22-121e-44a7-b78f-b19191810100",
                    "name": "Sci-Fi",
                },
            ],
        ),
        (
            "/api/v1/genres/",
            {"page_size": 1, "page_number": 2},
            200,
            [
                {
                    "id": "fb111f22-121e-44a7-b78f-b19191810100",
                    "name": "Sci-Fi",
                },
            ],
        ),
        (
            "/api/v1/genres/",
            {"page_size": 50, "page_number": 100},
            200,
            [],
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_genres_pagination(
    es_write_data: Any,
    es_genres_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: list[dict],
) -> None:
    """
    Тестирует получение всех жанров.
    """
    await write_data_to_es(es_write_data, es_genres_data, es_genres_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/genres/ef86b8ff-3c82-4d31-ad8e-72b69f4e3100/popular_films?page_size=50&page_number=1",
            {},
            200,
            [{"id": uuid} for uuid in UUIDS],
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_genre_cache(
    es_write_data: Any,
    es_genres_data: list[dict],
    es_movies_data: list[dict],
    clear_redis: Any,
    clear_es_indices: Any,
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: list[dict],
) -> None:
    """
    Тестирует получение данных жанра с учётом кеша в Redis.
    """
    await write_data_to_es(es_write_data, es_genres_data, es_genres_settings)
    await write_data_to_es(es_write_data, es_movies_data, es_movies_settings)
    status, body = await make_get_request(url, query_data)
    await clear_es_indices(es_movies_settings.es_index)
    status, body = await make_get_request(url, query_data)
    assert status == expected_status
    assert sorted([item["id"] for item in body]) == sorted(
        [item["id"] for item in expected_body]
    )
    await clear_redis()
    status, body = await make_get_request(url, query_data)
    assert status == 404
