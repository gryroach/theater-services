from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.v1.pagination import PaginationParams, get_pagination_params
from dependencies.services.person_service_factory import get_person_service
from dependencies.services.search_service_factory import (
    get_persons_search_service,
)
from models import FilmShort, Person
from models.search import PersonSearch
from services.person import PersonService
from services.search import SearchService

router = APIRouter()


@router.get("/search/", response_model=PersonSearch)
async def persons_search(
    query: str = Query(default=""),
    pagination_params: PaginationParams = Depends(get_pagination_params),
    search_service: SearchService = Depends(get_persons_search_service),
):
    persons = await search_service.search(
        query, pagination_params.page_size, pagination_params.page_number
    )
    return persons


@router.get("/", response_model=list[Person])
async def get_persons(
    pagination_params: PaginationParams = Depends(get_pagination_params),
    person_service: PersonService = Depends(get_person_service),
):
    persons = await person_service.get_all_persons(
        pagination_params.page_size, pagination_params.page_number
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
    pagination_params: PaginationParams = Depends(get_pagination_params),
    person_service: PersonService = Depends(get_person_service),
):
    films = await person_service.get_person_films(
        uuid, pagination_params.page_size, pagination_params.page_number
    )
    if not films:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Films not found for the person",
        )
    return films
