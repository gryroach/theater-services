from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from db.elastic import EsIndexes
from models import Film, FilmShort, FilmsSortOptions
from models.common import SearchResponse
from services.film import FilmService, get_film_service
from services.search import SearchService, get_search_service

router = APIRouter()


@router.get("/search/", response_model=SearchResponse)
async def films_search(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    query: str = Query(default=""),
    search_service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    films = await search_service.search(
        EsIndexes.movies.value, query, page_size, page_number
    )
    return films


@router.get("/{film_id}", response_model=Film)
async def film_details(
    film_id: str, film_service: FilmService = Depends(get_film_service)
) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="film not found"
        )

    return film


@router.get("/", response_model=list[FilmShort])
async def films_list(
    sort: FilmsSortOptions = Query(default=FilmsSortOptions.desc),
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    genre: UUID | None = Query(default=None),
    film_service: FilmService = Depends(get_film_service),
) -> list[FilmShort]:
    films = await film_service.get_films(sort, page_size, page_number, genre)
    return [FilmShort(**dict(film)) for film in films]
