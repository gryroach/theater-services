from .base_repositories import BaseElasticRepository, BaseRepositoryProtocol
from .film import FilmElasticRepository, FilmRepositoryProtocol
from .genre import GenreElasticRepository, GenreRepositoryProtocol
from .person import PersonElasticRepository, PersonRepositoryProtocol
from .search import SearchElasticRepository, SearchRepositoryProtocol, T

RepositoryType = (
    FilmRepositoryProtocol
    | GenreRepositoryProtocol
    | PersonRepositoryProtocol
    | SearchRepositoryProtocol[T]
)

__all__ = [
    "BaseRepositoryProtocol",
    "BaseElasticRepository",
    "FilmRepositoryProtocol",
    "FilmElasticRepository",
    "GenreRepositoryProtocol",
    "GenreElasticRepository",
    "PersonRepositoryProtocol",
    "PersonElasticRepository",
    "RepositoryType",
    "SearchRepositoryProtocol",
    "SearchElasticRepository",
]
