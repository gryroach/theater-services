import aiohttp
import pytest_asyncio
from tests.functional.settings import test_settings


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
