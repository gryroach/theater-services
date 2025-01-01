from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel):
    page: int
    has_next: bool


class PaginationResult(BaseModel, Generic[T]):
    pagination: Pagination
    data: list[T]


class Paginator(BaseModel, Generic[T]):
    page: int = Query(default=1, ge=1)
    size: int = Query(default=10, ge=1, le=50)

    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size

    def to_response(self, data: list) -> PaginationResult:
        """Формат ответа с метаданными пагинации."""
        return PaginationResult[T](
            pagination=Pagination(
                page=self.page,
                has_next=len(data) == self.size,
            ),
            data=data,
        )
