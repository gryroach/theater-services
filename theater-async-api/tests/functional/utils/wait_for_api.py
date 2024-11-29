import asyncio
import logging

import aiohttp
import backoff
from functional.settings import test_settings

logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, ConnectionError, max_tries=10)
async def api_resource_is_available() -> bool:
    """Проверяет доступность API-ресурса."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_settings.service_url, timeout=2):
                logging.info("Соединение с theater api services установленно")
                return True
        except Exception:
            raise ConnectionError


if __name__ == "__main__":
    asyncio.run(api_resource_is_available())
