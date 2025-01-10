import secrets
import string
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from exceptions import InvalidCredentialsError
from exceptions.auth_exceptions import InvalidProviderError
from exceptions.user_exceptions import (
    UserAlreadyExistsError,
    UserDoesNotExistsError,
)
from models import User
from repositories.user import UserRepository
from repositories.user_social_network import UserSocialNetworkRepository
from schemas.role import Role, UpdateRole
from schemas.user import (
    UserCreate,
    UserCredentials,
    UserCredentialsUpdate,
    UserData,
    UserEmailRegister,
    UserInDB,
    UserRegister,
)
from schemas.user_social_network import UserSocialNetworkCreate
from services.oauth import PROVIDERS
from services.roles import Roles
from services.session_service import SessionService, get_session_service


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        user_network_repo: UserSocialNetworkRepository,
        session_service: SessionService,
    ):
        self.user_repo = user_repo
        self.user_network_repo = user_network_repo
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

    async def register_user_by_oauth(
        self, db: AsyncSession, user_data: UserEmailRegister, provider: str
    ) -> tuple[User, str | None]:
        """
        Создание пользователя через его почту со случайным паролем.
        Если пользователь уже существует, он возвращается без пароля.
        """
        provider_service = PROVIDERS.get(provider)
        if not provider_service:
            raise InvalidProviderError(f"Unsupported provider: {provider}")
        provider_field = provider_service[1]

        user_social_network = await self.user_network_repo.get_by_field(db, provider_field, user_data.email)
        if user_social_network:
            return user_social_network.user, None

        alphabet = string.ascii_letters + string.digits
        user_login = "".join(secrets.choice(alphabet) for _ in range(8))
        user_password = "".join(secrets.choice(alphabet) for _ in range(8))

        user = await self.user_repo.create(
            db,
            obj_in=UserCreate(
                login=user_login,
                password=user_password,
                **user_data.model_dump(),
            ),
        )
        await self.session_service.set_session_version(str(user.id), 1)
        await self.user_network_repo.create(
            db,
            obj_in=UserSocialNetworkCreate(
                user_id=user.id,
                **{provider_field: user_data.email}
            )
        )
        return user, user_password


async def get_user_service(
    user_repo: Annotated[UserRepository, Depends()],
    user_network_repo: Annotated[UserSocialNetworkRepository, Depends()],
    token_service: Annotated[SessionService, Depends(get_session_service)],
) -> UserService:
    return UserService(user_repo=user_repo, user_network_repo=user_network_repo, session_service=token_service)
