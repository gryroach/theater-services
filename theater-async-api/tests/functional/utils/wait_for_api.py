import asyncio
import time

import aiohttp

from functional.settings import test_settings


async def api_resource_is_available():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(test_settings.service_url):
                return True
        except aiohttp.ClientError:
            return False


if __name__ == "__main__":
    while True:
        available = asyncio.run(api_resource_is_available())
        if available:
            break
        time.sleep(1)
