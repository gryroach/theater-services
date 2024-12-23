from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Type, TypeVar
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import delete, inspect, select
from sqlalchemy import update as sqlalchemy_update
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import Base


class Repository(ABC):

    @abstractmethod
    def get(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def get_multi(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def create(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def update(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def delete(self, *args, **kwargs):
        raise NotImplementedError


ModelType = TypeVar("ModelType", bound=Base)  # type: ignore
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class RepositoryDB(
    Repository, Generic[ModelType, CreateSchemaType, UpdateSchemaType]
):
    def __init__(self, model: Type[ModelType]):
        self._model = model

    async def get(self, db: AsyncSession, pk: UUID) -> Optional[ModelType]:
        statement = select(self._model).where(self._model.id == pk)
        results = await db.execute(statement=statement)
        return results.scalar_one_or_none()

    async def get_by_field(self, db: AsyncSession, field: str, value: Any):
        mapper = inspect(self._model)
        if field not in mapper.columns:
            raise ValueError(f"Поле '{field}' не существует")

        column = mapper.columns[field]
        if not column.unique and not column.primary_key:
            raise ValueError(
                f"Поле '{field}' не является уникальным или ключевым."
            )

        statement = select(self._model).where(
            getattr(self._model, field) == value
        )
        result = await db.execute(statement)
        return result.scalar_one_or_none()

    async def get_multi(
        self, db: AsyncSession, *, skip=0, limit=100
    ) -> list[ModelType]:
        statement = select(self._model).offset(skip).limit(limit)
        results = await db.execute(statement=statement)
        return results.scalars().all()

    async def get_by_field_multi(
        self, db: AsyncSession, field: str, value: Any, skip=0, limit=100
    ) -> list[ModelType]:
        mapper = inspect(self._model)
        if field not in mapper.columns:
            raise ValueError(f"Поле '{field}' не существует")

        statement = (
            select(self._model)
            .where(getattr(self._model, field) == value)
            .offset(skip)
            .limit(limit)
        )
        results = await db.execute(statement)
        return results.scalars().all()

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self._model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        obj_in_data = jsonable_encoder(obj_in)
        query = (
            sqlalchemy_update(self._model)
            .where(self._model.id == db_obj.id)
            .values(**obj_in_data)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, pk: UUID) -> None:
        query = delete(self._model).where(self._model.id == pk)
        result = await db.execute(query)
        affected_rows = result.rowcount
        await db.commit()
        if affected_rows == 0:
            raise NoResultFound
