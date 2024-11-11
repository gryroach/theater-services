from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from db.elastic import EsIndexes
from models import FilmShort, Person
from models.common import SearchResponse
from services.person import PersonService, get_person_service
from services.search import SearchService, get_search_service

router = APIRouter()


@router.get("/search/", response_model=SearchResponse)
async def films_search(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    query: str = Query(default=""),
    search_service: SearchService = Depends(get_search_service),
):
    persons = await search_service.search(
        EsIndexes.persons.value, query, page_size, page_number
    )
    return persons


@router.get("/", response_model=list[Person])
async def get_persons(
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    person_service: PersonService = Depends(get_person_service),
):
    persons = await person_service.get_all_persons(page_size, page_number)
    if not persons:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Persons not found"
        )
    return persons


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
    page_size: int = Query(default=10, ge=1, le=50),
    page_number: int = Query(default=1, ge=1),
    person_service: PersonService = Depends(get_person_service),
):
    films = await person_service.get_person_films(uuid, page_size, page_number)
    if not films:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Films not found for the person",
        )
    return films
