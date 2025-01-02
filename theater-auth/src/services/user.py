from typing import Annotated
from uuid import UUID

from exceptions import InvalidCredentialsError
from exceptions.user_exceptions import (
    UserAlreadyExistsError,
    UserDoesNotExistsError,
)
from fastapi import Depends
from repositories.user import UserRepository
from schemas.role import Role, UpdateRole
from schemas.user import (
    UserCreate,
    UserCredentials,
    UserCredentialsUpdate,
    UserData,
    UserInDB,
    UserRegister,
)
from services.roles import Roles
from services.session_service import SessionService, get_session_service
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        session_service: SessionService,
    ):
        self.user_repo = user_repo
        self.session_service = session_service

    async def register_user(
        self, db: AsyncSession, user_data: UserRegister
    ) -> UserInDB:
        existing_user = await self.user_repo.get_by_field(
            db, "login", user_data.login
        )
        if existing_user:
            raise UserAlreadyExistsError("Login already exists")
        user = await self.user_repo.create(
            db,
            obj_in=UserCreate(**user_data.model_dump()),
        )
        await self.session_service.set_session_version(str(user.id), 1)
        return UserInDB.model_validate(user)

    async def get_user_by_id(
        self, db: AsyncSession, user_id: UUID
    ) -> UserInDB:
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise UserDoesNotExistsError("User does not exist")
        return user

    async def get_user_role(self, db: AsyncSession, user_id: UUID) -> Role:
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise UserDoesNotExistsError("User does not exists")
        return getattr(Roles, user.role)

    async def update_role(
        self, db: AsyncSession, user_id: UUID, new_role: UpdateRole
    ) -> Role:
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise UserDoesNotExistsError("User does not exists")
        updated_user = await self.user_repo.update(
            db, db_obj=user, obj_in=new_role
        )
        return getattr(Roles, updated_user.role)

    async def update_credentials(
        self,
        db: AsyncSession,
        user_id: UUID,
        new_credentials: UserCredentialsUpdate,
    ) -> UserInDB:
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise UserDoesNotExistsError

        if not user.check_password(new_credentials.old_password):
            raise InvalidCredentialsError("Wrong login or password")

        user_credentials = UserCredentials(
            login=new_credentials.login, password=new_credentials.new_password
        )
        updated_user = await self.user_repo.update(
            db, db_obj=user, obj_in=user_credentials
        )
        return UserInDB.model_validate(updated_user)

    async def update_user_data(
        self,
        db: AsyncSession,
        user_id: UUID,
        user_data: UserData,
    ) -> UserData:
        user = await self.user_repo.get(db, user_id)
        if not user:
            raise UserDoesNotExistsError
        updated_user = await self.user_repo.update(
            db, db_obj=user, obj_in=user_data
        )
        return UserData.model_validate(updated_user)


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends()],
    token_service: Annotated[SessionService, Depends(get_session_service)],
) -> UserService:
    return UserService(user_repo=user_repo, session_service=token_service)
