from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from models.film import FilmShort
from models.person import Person
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get("/", response_model=list[Person])
async def get_genres(
    genre_service: PersonService = Depends(get_person_service),
):
    genres = await genre_service.get_all_persons()
    if not genres:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persons not found"
        )
    return genres


@router.get("/{uuid}", response_model=Person)
async def get_person(
    uuid: UUID,
    person_service: PersonService = Depends(get_person_service),
):
    person = await person_service.get_person_by_id(uuid)
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Person not found"
        )
    return person


@router.get("/{uuid}/film", response_model=list[FilmShort])
async def get_person_films(
    uuid: UUID,
    person_service: PersonService = Depends(get_person_service),
):
    films = await person_service.get_person_films(uuid)
    if not films:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Films not found for the person",
        )
    return films
