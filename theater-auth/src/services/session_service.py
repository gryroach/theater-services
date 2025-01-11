from core.config import settings
from db.redis import get_redis
from fastapi import Depends
from redis.asyncio import Redis
from repositories.cache import CacheRepository, RedisCacheRepository


class SessionService:
    """
    Сервис управлениями сессиями пользователей в кэш-сервисе
    """

    def __init__(self, cache: CacheRepository):
        self.cache = cache

    async def set_session_version(self, user_id: str, version: int):
        key = settings.SESSION_VERSION_KEY_TEMPLATE.format(user_id)
        await self.cache.set(key, version)

    async def get_session_version(self, user_id: str) -> int | None:
        key = settings.SESSION_VERSION_KEY_TEMPLATE.format(user_id)
        return await self.cache.get(key)

    async def invalidate_refresh_token(self, refresh_token: str, ttl: int):
        key = settings.INVALID_REFRESH_TOKEN_TEMPLATE.format(refresh_token)
        await self.cache.set(key, 1, expire=ttl)

    async def is_refresh_token_invalid(self, refresh_token: str) -> bool:
        key = settings.INVALID_REFRESH_TOKEN_TEMPLATE.format(refresh_token)
        return await self.cache.exists(key)

    async def increment_session_version(self, user_id: str) -> None:
        key = settings.SESSION_VERSION_KEY_TEMPLATE.format(user_id)
        current_version = await self.get_session_version(user_id)
        new_version = (int(current_version) or 0) + 1
        await self.cache.set(key, new_version)

    async def logout(self, refresh_token: str, ttl: int) -> None:
        await self.invalidate_refresh_token(refresh_token, ttl)

    async def logout_all(self, user_id: str) -> None:
        await self.increment_session_version(user_id)


async def get_session_service(
    redis: Redis = Depends(get_redis),
) -> SessionService:
    return SessionService(RedisCacheRepository(redis))
