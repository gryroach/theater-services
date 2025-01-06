import datetime

from core.config import settings
from db.redis import get_redis


class RateLimitService:
    """
    Сервис для ограничения количества запросов от одного IP-адреса.
    Используется скользящее временное окно в 60 секунд.

    Attributes:
        ip_address (str): IP-адрес, для которого применяется ограничение.
    """

    def __init__(self, ip_address: str) -> None:
        self.ip_address = ip_address

    async def __call__(self) -> None:
        if settings.test_mode:
            return None

        redis = await get_redis()
        pipe = redis.pipeline()

        now = datetime.datetime.now()
        window_start = now - datetime.timedelta(seconds=60)

        # Удаление записей для ключа, которые старше 1 минуты
        await pipe.zremrangebyscore(
            self.ip_address, 0, window_start.timestamp()
        )

        # Добавление текущего запроса
        await pipe.zadd(
            self.ip_address, {str(now.timestamp()): now.timestamp()}
        )

        await pipe.expire(self.ip_address, 60)

        # Количество запросов для ip-адреса в текущем временном окне
        await pipe.zcard(self.ip_address)

        result = await pipe.execute()
        request_number = result[-1]

        if request_number > settings.request_limit_per_minute:
            raise RateLimitException


class RateLimitException(Exception):
    pass
