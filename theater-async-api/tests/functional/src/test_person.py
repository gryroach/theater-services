import logging
from typing import Any

import pytest
from tests.functional.conftest import UUIDS
from tests.functional.settings import es_movies_settings, es_persons_settings
from tests.functional.utils.checks import fetch_and_check_response
from tests.functional.utils.es_helpers import write_data_to_es

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        ("/api/v1/persons/invalid_uuid", {}, 422, {"detail": "Invalid UUID"}),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_invalid_uuid(
    es_write_data: Any,
    es_persons_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: dict,
) -> None:
    """
    Тестирует обработку некорректного UUID.
    """
    await write_data_to_es(es_write_data, es_persons_data, es_persons_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/persons/ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95",
            {},
            200,
            {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95", "full_name": "Ann"},
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_valid_uuid(
    es_write_data: Any,
    es_persons_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: dict,
) -> None:
    """
    Тестирует обработку корректного UUID.
    """
    await write_data_to_es(es_write_data, es_persons_data, es_persons_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/persons/fb111f22-121e-44a7-b78f-b19191810fbf/film?page_size=50&page_number=1",
            {},
            200,
            [{"id": uuid} for uuid in UUIDS],
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_person_films(
    es_write_data: Any,
    es_persons_data: list[dict],
    es_movies_data,
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: list[dict],
) -> None:
    """
    Тестирует получение фильмов для персоны.
    """
    await write_data_to_es(es_write_data, es_persons_data, es_persons_settings)
    await write_data_to_es(es_write_data, es_movies_data, es_movies_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/persons/",
            {},
            200,
            [
                {"id": "ef86b8ff-3c82-4d31-ad8e-72b69f4e3f95"},
                {"id": "fb111f22-121e-44a7-b78f-b19191810fbf"},
                {"id": "caf76c67-c0fe-477e-8766-3ab3ff2574b5"},
                {"id": "b45bd7bc-2e16-46d5-b125-983d356768c6"},
                {"id": "4c1d0404-075e-4027-b4ae-01d5d4a10a9b"},
            ],
        ),
        (
            "/api/v1/persons/",
            {"page_size": 3, "page_number": 2},
            200,
            [
                {"id": "b45bd7bc-2e16-46d5-b125-983d356768c6"},
                {"id": "4c1d0404-075e-4027-b4ae-01d5d4a10a9b"},
            ],
        ),
        (
            "/api/v1/persons/",
            {"page_size": 10, "page_number": 5},
            200,
            [],
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_person_pagination(
    es_write_data: Any,
    es_persons_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: list[dict],
) -> None:
    """
    Тестирует получение всех персон.
    """
    await write_data_to_es(es_write_data, es_persons_data, es_persons_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/persons/fb111f22-121e-44a7-b78f-b19191810fbf/film?page_size=50&page_number=1",
            {},
            200,
            [{"id": uuid} for uuid in UUIDS],
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_person_films_cache(
    es_write_data: Any,
    es_persons_data: list[dict],
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
    Тестирует получение данных с учётом кеша в Redis.
    """
    await write_data_to_es(es_write_data, es_persons_data, es_persons_settings)
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
