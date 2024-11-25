import json
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel
from pydantic.json import pydantic_encoder

from services.repositories import RepositoryType

T = TypeVar("T", bound=BaseModel)


class CacheServiceInterface(Protocol):
    async def set(  # noqa: A003
            self, key: str, value: Any, expire: int
    ) -> None:
        pass

    async def get(self, key: str) -> Any:
        pass


class CacheServiceMixin:
    def __init__(
        self,
        cache_service: CacheServiceInterface,
        key_prefix: str = "",
        cache_expire: int = 60,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.cache_service = cache_service
        self.key_prefix = key_prefix
        self.cache_expire = cache_expire

    async def put_into_cache(self, data: T | list[T], /, **kwargs: Any):
        value = json.dumps(data, default=pydantic_encoder)
        key = self._generate_key(self.key_prefix, **kwargs)
        await self.cache_service.set(key, value, self.cache_expire)

    async def get_data_from_cache(
        self, model: type[BaseModel], single: bool = False, /, **kwargs: Any
    ) -> T | list[T] | None:
        key = self._generate_key(self.key_prefix, **kwargs)

        data = await self.cache_service.get(key)
        if not data:
            return None

        if single:
            return model.model_validate_json(data)

        data = json.loads(data)
        return [model.model_validate(d) for d in data]

    @staticmethod
    def _generate_key(key_prefix: str, /, **kwargs: Any) -> str:
        parts = [key_prefix]
        for key, value in kwargs.items():
            parts.append(f"{key}_{value}")
        return "_".join(parts)


class BaseService(CacheServiceMixin):
    def __init__(
        self,
        repository: RepositoryType,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.repository = repository
        super().__init__(*args, **kwargs)
