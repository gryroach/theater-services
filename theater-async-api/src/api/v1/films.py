<<<<<<< HEAD
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.enums import FilmsSortOptions
from models.film import Film, FilmShort
=======
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

>>>>>>> main
from services.film import FilmService, get_film_service

router = APIRouter()


<<<<<<< HEAD
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
        page_size: Optional[int] = Query(default=10, ge=1, le=50),
        page_number: Optional[int] = Query(default=1, ge=1),
        genre: Optional[UUID] = Query(default=None),
        film_service: FilmService = Depends(get_film_service),
) -> list[FilmShort]:
    films = await film_service.get_films(sort, page_size, page_number, genre)
    return [FilmShort(**dict(film)) for film in films]
=======
class Film(BaseModel):
    id: str
    title: str


@router.get('/{film_id}', response_model=Film)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return Film(id=film.id, title=film.title)
>>>>>>> main
