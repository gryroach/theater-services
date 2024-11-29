import logging

import backoff
from functional.settings import test_settings
from redis import Redis

logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, ConnectionError, max_tries=10)
def is_redis_available() -> bool:
    """Проверяет доступность Redis."""
    redis_client = Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
        socket_connect_timeout=1,
    )
    if redis_client.ping():
        logging.info("Соединение с Redis установленно")
    else:
        raise ConnectionError


if __name__ == "__main__":
    is_redis_available()
