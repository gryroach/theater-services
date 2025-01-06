from datetime import date
from typing import Annotated

from fastapi import Depends
from repositories.login_history import LoginHistoryRepository
from schemas.login import LoginHistoryCreate, LoginHistoryInDB
from sqlalchemy.ext.asyncio import AsyncSession


class LoginHistoryService:
    def __init__(self, repo: LoginHistoryRepository):
        self.repo = repo

    async def log_login(self, db: AsyncSession, data: LoginHistoryCreate):
        """Записать вход в историю с учётом партицирования."""
        return await self.repo.create(db, obj_in=data)

    async def get_user_history(
        self, db: AsyncSession, user_id: str, skip: int, limit: int
    ) -> list[LoginHistoryInDB]:
        """Получить историю входов для конкретного пользователя с пагинацией."""
        history = await self.repo.get_by_field_multi(
            db, field="user_id", value=user_id, skip=skip, limit=limit
        )
        return [LoginHistoryInDB.model_validate(record) for record in history]


async def get_login_history_service(
    repo: Annotated[LoginHistoryRepository, Depends()],
) -> LoginHistoryService:
    return LoginHistoryService(repo=repo)
