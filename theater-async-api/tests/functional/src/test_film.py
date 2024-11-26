import uuid
from http import HTTPStatus

import pytest
from tests.functional.settings import es_movies_settings


PAGE_SIZE = 20
LENGTH = 10

@pytest.mark.asyncio(loop_scope="session")
async def test_film_success(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    film_id,
    imdb_rating,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)
    expected_body = {
        "id": film_id,
        "title": "The Star",
        "imdb_rating": imdb_rating(film_id),
        "description": "New World",
        "genres": [
            "Action",
            "Sci-Fi"
        ]
    }

    url = f"/api/v1/films/{film_id}"
    status, body = await make_get_request(url)

    assert status == HTTPStatus.OK
    assert body == expected_body


@pytest.mark.asyncio(loop_scope="session")
async def test_film_fail(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)
    movie_id = str(uuid.uuid4())
    url = f"/api/v1/films/{movie_id}"
    status, body = await make_get_request(url)

    assert status == HTTPStatus.NOT_FOUND


@pytest.mark.asyncio(loop_scope="session")
async def test_films(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    expected_body,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)

    url = f"/api/v1/films/"
    status, body = await make_get_request(url)

    assert status == HTTPStatus.OK
    assert body == expected_body[:LENGTH]


@pytest.mark.asyncio(loop_scope="session")
async def test_films_pagination(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    expected_body,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)

    url = f"/api/v1/films/?page_size={PAGE_SIZE}"
    status, body = await make_get_request(url)

    assert status == HTTPStatus.OK
    assert body == expected_body[:PAGE_SIZE]


@pytest.mark.parametrize(
    "url, reverse", [
        ("/api/v1/films/", True),
        ("/api/v1/films/?sort=imdb_rating", False)
    ]
)
@pytest.mark.asyncio(loop_scope="session")
async def test_sort_films(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    url: str,
    reverse: bool,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)

    status, body = await make_get_request(url)
    ratings = [film["imdb_rating"] for film in body]

    assert status == HTTPStatus.OK
    assert ratings == sorted(ratings, reverse=reverse)

@pytest.mark.parametrize(
    "genre, expected_answer", [
        (
            {"genre": "fb111f22-121e-44a7-b78f-b19191810100"},
            {"status": HTTPStatus.OK, "length": LENGTH}
        ),
        (
            {"genre": "fb111f22-121e-44a7-b78f-b19191810111"},
            {"status": HTTPStatus.OK, "length": 0}
        ),
    ]
)
@pytest.mark.asyncio(loop_scope="session")
async def test_films_by_genre(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    genre,
    expected_answer,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)

    url = "/api/v1/films/"
    status, body = await make_get_request(url, genre)

    assert status == expected_answer["status"]
    assert len(body) == expected_answer["length"]

    for film in body:
        url = f"/api/v1/films/{film['id']}"
        status, movie = await make_get_request(url)
        assert "Sci-Fi" in movie["genres"]
