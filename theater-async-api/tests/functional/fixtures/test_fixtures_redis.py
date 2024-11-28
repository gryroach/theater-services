import pytest
import pytest_asyncio
from redis.asyncio import Redis
from tests.functional.settings import test_settings


@pytest_asyncio.fixture(name="redis_client", scope="session")
async def redis_client() -> Redis:
    """
    Создает асинхронного клиента Redis для использования в тестах.
    """
    client = Redis(host=test_settings.redis_host, port=test_settings.redis_port)
    yield client
    await client.aclose()


@pytest.fixture(autouse=True)
async def clear_cache(redis_client: Redis):
    """
    Очищает Redis по завершению теста.
    """
    yield
    await redis_client.flushall()


@pytest_asyncio.fixture(name="clear_redis")
def clear_redis(redis_client: Redis):
    """
    Очищает Redis.
    """

    async def inner() -> None:
        await redis_client.flushall()

    return inner
