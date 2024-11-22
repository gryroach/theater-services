import json
from typing import Any, TypeVar, Protocol

from elasticsearch import AsyncElasticsearch
from pydantic import BaseModel
from pydantic.json import pydantic_encoder

T = TypeVar("T", bound=BaseModel)


class CacheService(Protocol):
    async def set(self, key: str, value: Any, expire: int) -> None:
        pass

    async def get(self, key: str) -> Any:
        pass


class BaseCacheService:
    def __init__(
        self,
        cache_service: CacheService,
        elastic: AsyncElasticsearch,
        index_name: str,
        cache_expire: int = 60,
    ):
        self.cache_service = cache_service
        self.elastic = elastic
        self.index_name = index_name
        self.cache_expire = cache_expire

    async def put_into_cache(self, data: T | list[T], /, **kwargs: Any):
        value = json.dumps(data, default=pydantic_encoder)
        key = self._generate_key(self.index_name, **kwargs)
        await self.cache_service.set(key, value, self.cache_expire)

    async def get_data_from_cache(
        self, model: type[BaseModel], single: bool = False, /, **kwargs: Any
    ) -> T | list[T] | None:
        key = self._generate_key(self.index_name, **kwargs)

        data = await self.cache_service.get(key)
        if not data:
            return None

        if single:
            return model.model_validate_json(data)

        data = json.loads(data)
        return [model.model_validate(d) for d in data]

    @staticmethod
    def _generate_key(index_name: str, /, **kwargs: Any) -> str:
        parts = [index_name]
        for key, value in kwargs.items():
            parts.append(f"{key}_{value}")
        return "_".join(parts)
