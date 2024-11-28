from fastapi import Query
from pydantic import BaseModel


class PaginationParams(BaseModel):
    page_size: int
    page_number: int


def get_pagination_params(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
) -> PaginationParams:
    return PaginationParams(page_size=page_size, page_number=page_number)
