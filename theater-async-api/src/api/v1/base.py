from fastapi import APIRouter

from api.v1.films import router as film_router
from api.v1.genre import router as genre_router
from api.v1.person import router as person_router

api_router = APIRouter()
api_router.include_router(film_router, prefix="/films", tags=["films"])
api_router.include_router(genre_router, prefix="/genres", tags=["genres"])
api_router.include_router(person_router, prefix="/persons", tags=["persons"])
