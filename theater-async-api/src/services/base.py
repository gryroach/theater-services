import json
from typing import Any, TypeVar

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel
from redis.asyncio import Redis

T = TypeVar("T", bound=BaseModel)


class BaseEsService:
    def __init__(
        self,
        redis: Redis,
        elastic: AsyncElasticsearch,
        index_name: str,
        model: type[BaseModel],
        cache_expire: int = 60,
    ):
        self.redis = redis
        self.elastic = elastic
        self.index_name = index_name
        self.model = model
        self.cache_expire = cache_expire

    async def put_into_cache(self, data: T | list[T], /, **kwargs: Any):
        value = (
            json.dumps([d.model_dump_json() for d in data])
            if isinstance(data, list)
            else data.model_dump_json()
        )

        key = self._generate_key(self.index_name, **kwargs)
        await self.redis.set(key, value, self.cache_expire)

    async def get_data_from_cache(
        self, single: bool = False, /, **kwargs: Any
    ) -> T | list[T] | None:
        key = self._generate_key(self.index_name, **kwargs)

        data = await self.redis.get(key)
        if not data:
            return None

        if single:
            return self.model.model_validate_json(data)

        data = json.loads(data)
        return [self.model.model_validate(d) for d in data]

    @staticmethod
    def _generate_key(index_name: str, /, **kwargs: Any) -> str:
        parts = [index_name]
        for key, value in kwargs.items():
            parts.append(f"{key}_{value}")
        return "_".join(parts)
