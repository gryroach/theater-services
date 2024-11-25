from typing import Any

from tests.functional.conftest import STATUSES_WITH_DYNAMIC_BODY


async def fetch_and_check_response(
    make_get_request: Any,
    url: str,
    query_data: dict,
    expected_status: int,
    expected_body: Any,
) -> None:
    """
    Делает запрос и проверяет ответ.

    Args:
        make_get_request (Any): Фикстура для GET-запроса.
        url (str): URL для запроса.
        query_data (dict): Параметры запроса.
        expected_status (int): Ожидаемый HTTP-статус.
        expected_body (Any): Ожидаемое тело ответа.
    """
    status, body = await make_get_request(url, query_data)
    check_status(status, expected_status)
    if expected_status not in STATUSES_WITH_DYNAMIC_BODY:
        check_body(body, expected_body)


def check_status(status: int, expected_status: int) -> None:
    """
    Проверяет статус ответа.

    Args:
        status (int): Реальный статус ответа.
        expected_status (int): Ожидаемый статус ответа.

    Raises:
        AssertionError: Если статус не соответствует ожидаемому.
    """
    assert (
        status == expected_status
    ), f"Expected {expected_status}, got {status}"


def check_body(body: Any, expected_body: Any) -> None:
    """
    Проверяет тело ответа.

    Args:
        body (Any): Реальное тело ответа.
        expected_body (Any): Ожидаемое тело ответа.

    Raises:
        AssertionError: Если тело не соответствует ожидаемому.
    """
    if isinstance(expected_body, dict):
        for key, value in expected_body.items():
            assert (
                body.get(key) == value
            ), f"Key '{key}' mismatch: {body.get(key)} != {value}"
    elif isinstance(expected_body, list):
        assert sorted([item["id"] for item in body]) == sorted(
            [item["id"] for item in expected_body]
        ), "Mismatch in list IDs"
