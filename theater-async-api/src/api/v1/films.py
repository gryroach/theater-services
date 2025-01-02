from uuid import UUID

from api.v1.pagination import PaginationParams
from dependencies.services.film_service_factory import get_film_service
from dependencies.services.search_service_factory import (
    get_films_search_service,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status
from models import Film, FilmShort, FilmsSortOptions
from models.search import FilmSearch
from security.dependencies import security_jwt
from services.film import FilmService
from services.search import SearchService

router = APIRouter()


@router.get("/search/", response_model=FilmSearch)
async def films_search(
    query: str = Query(default=""),
    pagination_params: PaginationParams = Depends(PaginationParams),
    search_service: SearchService = Depends(get_films_search_service),
    user: dict = Depends(security_jwt),
) -> FilmSearch:
    films = await search_service.search(
        query, pagination_params.page_size, pagination_params.page_number
    )
    return films


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: str,
    film_service: FilmService = Depends(get_film_service),
    user: dict = Depends(security_jwt),
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
    pagination_params: PaginationParams = Depends(PaginationParams),
    genre: UUID | None = Query(default=None),
    film_service: FilmService = Depends(get_film_service),
    user: dict = Depends(security_jwt),
) -> list[FilmShort]:
    films = await film_service.get_films(
        sort, pagination_params.page_size, pagination_params.page_number, genre
    )
    return [FilmShort(**dict(film)) for film in films]
