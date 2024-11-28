from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.v1.pagination import PaginationParams, get_pagination_params
from dependencies.services.film_service_factory import get_film_service
from dependencies.services.search_service_factory import (
    get_films_search_service,
)
from models import Film, FilmShort, FilmsSortOptions
from models.search import FilmSearch
from services.film import FilmService
from services.search import SearchService

router = APIRouter()


@router.get("/search/", response_model=FilmSearch)
async def films_search(
    query: str = Query(default=""),
    pagination_params: PaginationParams = Depends(get_pagination_params),
    search_service: SearchService = Depends(get_films_search_service),
) -> FilmSearch:
    films = await search_service.search(
        query, pagination_params.page_size, pagination_params.page_number
    )
    return films


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_film_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="film not found"
        )
    return film


@router.get("/", response_model=list[FilmShort])
async def films_list(
    sort: FilmsSortOptions = Query(default=FilmsSortOptions.desc),
    pagination_params: PaginationParams = Depends(get_pagination_params),
    genre: UUID | None = Query(default=None),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmShort]:
    films = await film_service.get_films(
        sort, pagination_params.page_size, pagination_params.page_number, genre
    )
    return [FilmShort(**dict(film)) for film in films]
