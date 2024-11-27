import logging
from typing import Generic, Protocol, TypeVar
from uuid import UUID

from elasticsearch import AsyncElasticsearch, NotFoundError
from pydantic import ValidationError

from models import Film, FilmShort, Genre, Person

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=FilmShort | Film | Genre | Person)
V = TypeVar("V", bound=FilmShort | Film | Genre | Person)


class BaseRepositoryProtocol(Protocol[T, V]):
    async def get_by_id(self, id_: UUID) -> T | None: ...

    async def get_all(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[V]: ...


class BaseElasticRepository(Generic[T, V]):
    """
    Базовый класс для репозиториев, работающих с Elasticsearch.

    Этот класс предоставляет базовые методы для получения данных
    из Elasticsearch, такие как получение документа по идентификатору
    и получение всех документов с пагинацией.

    Attributes:
        index_name (str): Название индекса Elasticsearch.
        elastic (AsyncElasticsearch): Клиент Elasticsearch.
        t_model_class (Type[T]): Класс модели для типа T.
        v_model_class (Type[V]): Класс модели для типа V.
    """

    def __init__(
        self,
        index_name: str,
        elastic: AsyncElasticsearch,
        t_model_class: type[T],
        v_model_class: type[V],
    ):
        self.index_name = index_name
        self.elastic = elastic
        self.t_model_class = t_model_class
        self.v_model_class = v_model_class

    async def get_by_id(self, id_: UUID) -> T | None:
        """
        Получение документа по идентификатору.

        Args:
            id_ (UUID): Идентификатор документа.

        Returns:
            Optional[T]: Экземпляр модели T или None, если документ не найден.
        """
        try:
            doc = await self.elastic.get(index=self.index_name, id=str(id_))
        except NotFoundError:
            return None
        try:
            return self.t_model_class(**doc["_source"])
        except ValidationError as e:
            logger.error(f"Ошибка создания {self.t_model_class.__name__}: {e}")
            return None

    async def get_all(
        self,
        page_size: int,
        page_number: int,
        sort: str | None = None,
    ) -> list[V]:
        """
        Получение всех документов с пагинацией и сортировкой.

        Args:
            page_size (int): Размер страницы.
            page_number (int): Номер страницы.
            sort (Optional[str]): Поле для сортировки.

        Returns:
            List[V]: Список экземпляров модели V.
        """
        query: dict = {"match_all": {}}
        return await self._get_paginated_result(
            query, page_size, page_number, sort
        )

    async def _get_paginated_result(
        self,
        query: dict,
        page_size: int,
        page_number: int,
        sort: str | None = None,
        index_name: str | None = None,
        model: type[V] | None = None,
    ) -> list[V]:
        """
        Внутренний метод для получения пагинированного результата.

        Args:
            query (Dict): Запрос Elasticsearch.
            page_size (int): Размер страницы.
            page_number (int): Номер страницы.
            sort (Optional[str]): Поле для сортировки.
            index_name (Optional[str]): Имя индекса Elasticsearch.
            model (Optional[Type[V]]): Класс модели для типа V.

        Returns:
            List[V]: Список экземпляров модели V.
        """
        index_name = index_name or self.index_name
        model = model or self.v_model_class

        body = {
            "query": query,
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }

        if sort is not None:
            order, row = (
                ("desc", sort[1:]) if sort[0] == "-" else ("asc", sort)
            )
            body["sort"] = [{row: {"order": order}}]
        hits = []
        try:
            docs = await self.elastic.search(index=index_name, body=body)
            hits = [model(**hit["_source"]) for hit in docs["hits"]["hits"]]
        except NotFoundError as e:
            logger.error(f"Индекс не найден: {index_name}. Ошибка: {e}")
        except ValidationError as e:
            logger.error(f"Ошибка создания {model.__name__}: {e}")
        return hits
