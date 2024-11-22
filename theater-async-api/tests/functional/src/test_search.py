import pytest
from tests.functional.settings import es_movies_settings


@pytest.mark.parametrize(
    "query_data, expected_answer",
    [
        ({"query": "The Star"}, {"status": 200, "count": 60, "length": 10}),
        ({"query": "Mashed potato"}, {"status": 200, "count": 0, "length": 0}),
    ],
)
@pytest.mark.asyncio(loop_scope="session")
async def test_search_films(
    es_write_data,
    make_get_request,
    es_movies_data: list[dict],
    query_data: dict,
    expected_answer: dict,
) -> None:
    await es_write_data(es_movies_data, es_movies_settings.es_index)

    url = "/api/v1/films/search/"
    status, body = await make_get_request(url, query_data)

    assert status == expected_answer["status"]
    assert len(body["result"]) == expected_answer["length"]
    assert body["count"] == expected_answer["count"]
