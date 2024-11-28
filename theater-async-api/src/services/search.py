from typing import Generic, TypeVar

from models import FilmShort, Genre, Person
from models.search import SearchResponse
from services.base import BaseService

T = TypeVar("T", bound=FilmShort | Genre | Person)


class SearchService(BaseService, Generic[T]):
    async def search(
        self,
        query_string: str,
        page_size: int,
        page_number: int,
    ) -> SearchResponse[T]:
        result = await self.get_data_from_cache(
            SearchResponse,
            True,
            query_string=query_string,
            page_size=page_size,
            page_number=page_number,
        )
        if not result:
            result = await self.repository.get_search_result(
                query_string=query_string,
                page_size=page_size,
                page_number=page_number,
            )
            await self.put_into_cache(
                result,
                query_string=query_string,
                page_size=page_size,
                page_number=page_number,
            )
        return result
