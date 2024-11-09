from typing import List
from uuid import UUID

from db.elastic import get_elastic
from fastapi import APIRouter, Depends, HTTPException
from models.film import Film, FilmShort
from models.genre import Genre
from services.genre import GenreService

router = APIRouter()


async def get_genre_service(elastic=Depends(get_elastic)):
    return GenreService(elastic)


@router.get("/", response_model=List[Genre])
async def get_genres(genre_service: GenreService = Depends(get_genre_service)):
    genres = await genre_service.get_all_genres()
    if not genres:
        raise HTTPException(status_code=404, detail="Genres not found")
    return genres


@router.get("/{uuid}", response_model=Genre)
async def get_genre(
    uuid: UUID, genre_service: GenreService = Depends(get_genre_service)
):
    genre = await genre_service.get_genre_by_id(uuid)
    if not genre:
        raise HTTPException(status_code=404, detail="Genre not found")
    return genre


@router.get("/{uuid}/popular_films", response_model=List[FilmShort])
async def get_popular_films_by_genre(
    uuid: UUID,
    page_size: int = 10,
    page_number: int = 1,
    genre_service: GenreService = Depends(get_genre_service),
):
    films = await genre_service.get_popular_films(uuid, page_size, page_number)
    if not films:
        raise HTTPException(
            status_code=404, detail="No films found for this genre"
        )
    return films
