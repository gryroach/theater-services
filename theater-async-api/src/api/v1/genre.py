from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from models import FilmShort, Genre
from models.search import GenreSearch
from services.genre import GenreService, get_genre_service
from services.search import SearchService, get_genres_search_service

router = APIRouter()


@router.get("/search/", response_model=GenreSearch)
async def genres_search(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    query: str = Query(default=""),
    search_service: SearchService = Depends(get_genres_search_service),
):
    genres = await search_service.search(query, page_size, page_number)
    return genres


@router.get("/", response_model=list[Genre])
async def get_genres(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    genre_service: GenreService = Depends(get_genre_service),
):
    genres = await genre_service.get_all_genres(page_size, page_number)
    return genres


@router.get("/{uuid}", response_model=Genre)
async def get_genre(
    uuid: UUID, genre_service: GenreService = Depends(get_genre_service)
):
    genre = await genre_service.get_genre_by_id(uuid)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Genre not found"
        )
    return genre


@router.get("/{uuid}/popular_films", response_model=list[FilmShort])
async def get_popular_films_by_genre(
    uuid: UUID,
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    genre_service: GenreService = Depends(get_genre_service),
):
    films = await genre_service.get_popular_films(uuid, page_size, page_number)
    if not films:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No films found for this genre",
        )
    return films
