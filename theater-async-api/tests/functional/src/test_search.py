from typing import Any

import pytest
from tests.functional.settings import (
    es_genres_settings,
    es_movies_settings,
    es_persons_settings,
)
from tests.functional.utils.checks import fetch_and_check_response
from tests.functional.utils.es_helpers import write_data_to_es


@pytest.mark.parametrize(
    "index_name, url, es_data_fixture, query_data, expected_answer",
    [
        # Тесты для фильмов
        (
            "movies",
            "/api/v1/films/search/",
            "es_movies_data",
            {"query": "The Star", "page_size": 10},
            {"status": 200, "count": 40, "length": 10},
        ),
        (
            "movies",
            "/api/v1/films/search/",
            "es_movies_data",
            {"query": "Mashed potato"},
            {"status": 200, "count": 0, "length": 0},
        ),
        (
            "movies",
            "/api/v1/films/search/",
            "es_movies_data",
            {"query": '"The Star"'},
            {"status": 200, "count": 40, "length": 10},
        ),
        # Тесты для жанров
        (
            "genres",
            "/api/v1/genres/search/",
            "es_genres_data",
            {"query": "Action", "page_size": 10},
            {"status": 200, "count": 1, "length": 1},
        ),
        (
            "genres",
            "/api/v1/genres/search/",
            "es_genres_data",
            {"query": "Nonexistent"},
            {"status": 200, "count": 0, "length": 0},
        ),
        (
            "genres",
            "/api/v1/genres/search/",
            "es_genres_data",
            {"query": '"Action"'},
            {"status": 200, "count": 1, "length": 1},
        ),
        # Тесты для персон
        (
            "persons",
            "/api/v1/persons/search/",
            "es_persons_data",
            {"query": "Ann", "page_size": 10},
            {"status": 200, "count": 1, "length": 1},
        ),
        (
            "persons",
            "/api/v1/persons/search/",
            "es_persons_data",
            {"query": "Unknown"},
            {"status": 200, "count": 0, "length": 0},
        ),
        (
            "persons",
            "/api/v1/persons/search/",
            "es_persons_data",
            {"query": '"Ann"'},
            {"status": 200, "count": 1, "length": 1},
        ),
        # Сложные фразы
        (
            "movies",
            "/api/v1/films/search/",
            "es_movies_data",
            {"query": 'The Star AND "Potato"', "page_size": 10},
            {"status": 200, "count": 40, "length": 10},
        ),
        (
            "movies",
            "/api/v1/films/search/",
            "es_movies_data",
            {
                "query": 'The Star OR "Potato"',
                "page_size": 10,
            },
            {"status": 200, "count": 40, "length": 10},
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_search_entities(
    es_write_data: Any,
    make_get_request: Any,
    request: Any,
    index_name: str,
    url: str,
    es_data_fixture: str,
    query_data: dict,
    expected_answer: dict,
) -> None:
    """
    Унифицированный тест для поиска в индексах фильмов, жанров и персон.
    """
    es_data = request.getfixturevalue(es_data_fixture)
    es_settings = {
        "movies": es_movies_settings,
        "genres": es_genres_settings,
        "persons": es_persons_settings,
    }[index_name]
    await es_write_data(es_data, es_settings.es_index)

    status, body = await make_get_request(url, query_data)

    assert status == expected_answer["status"]
    assert len(body["result"]) == expected_answer["length"]
    assert body["count"] == expected_answer["count"]


@pytest.mark.parametrize(
    "url, query_data, expected_status, expected_body",
    [
        (
            "/api/v1/films/search/",
            {"query": "", "page_size": 10},
            200,
            {"count": 0, "result": []},
        ),
        (
            "/api/v1/genres/search/",
            {"query": "", "page_size": 10},
            200,
            {"count": 0, "result": []},
        ),
        (
            "/api/v1/persons/search/",
            {"query": "", "page_size": 10},
            200,
            {"count": 0, "result": []},
        ),
        (
            "/api/v1/films/search/",
            {"query": "star", "page_size": 0},
            422,
            {"detail": "Page size must be at least 1"},
        ),
        (
            "/api/v1/films/search/",
            {"query": "star", "page_number": -1},
            422,
            {"detail": "Page number must be positive"},
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_search_validation_and_limit(
    es_write_data: Any,
    es_movies_data: list[dict],
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: Any,
) -> None:
    """
    Тесты на граничные случаи валидации и ограничение количества записей.
    """
    await write_data_to_es(es_write_data, es_movies_data, es_movies_settings)
    await fetch_and_check_response(
        make_get_request, url, query_data, expected_status, expected_body
    )


@pytest.mark.parametrize(
    "url, query_data, expected_status, empty_result_body",
    [
        (
            "/api/v1/films/search/",
            {"query": "The Star"},
            200,
            {"count": 0, "result": []},
        ),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_film_search_cache(
    es_write_data: Any,
    es_movies_data: list[dict],
    clear_redis: Any,
    clear_es_indices: Any,
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: list[dict],
    empty_result_body: list[dict],
    search_expected_body: dict,
) -> None:
    """
    Тест поиска фильмов с использованием кеша в Redis.
    """
    # Загружаем данные в Elasticsearch
    await write_data_to_es(es_write_data, es_movies_data, es_movies_settings)
    # Выполняем первый запрос, данные кэшируются
    status, body = await make_get_request(url, query_data)
    assert status == expected_status
    assert body == search_expected_body
    # Очищаем данные в Elasticsearch, но кэш не трогаем
    await clear_es_indices(es_movies_settings.es_index)
    # Выполняем запрос повторно, данные должны вернуться из кэша
    status, body_cached = await make_get_request(url, query_data)
    assert status == expected_status
    assert body_cached == search_expected_body
    # Очищаем кэш
    await clear_redis()
    # Выполняем запрос, должно вернуться тело запроса с пустым списком
    status, body_after_clear_cache = await make_get_request(url, query_data)
    assert status == 200
    assert body_after_clear_cache == empty_result_body
