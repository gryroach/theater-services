from datetime import timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.enums import PayloadKeys, TokenTypes
from exceptions.auth_exceptions import (
    InvalidCredentialsError,
    InvalidSessionError,
)
from repositories.user import UserRepository
from schemas.login import LoginHistoryCreate
from schemas.refresh import TokenResponse
from services.jwt_service import JWTService, get_jwt_service
from services.login_history import (
    LoginHistoryService,
    get_login_history_service,
)
from services.session_service import SessionService, get_session_service


class AuthService:
    def __init__(
        self,
        user_repo: UserRepository,
        history_service: LoginHistoryService,
        session_service: SessionService,
        jwt_service: JWTService,
    ):
        self.user_repo = user_repo
        self.history_service = history_service
        self.session_service = session_service
        self.jwt_service = jwt_service
        self.access_ttl = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
        self.refresh_ttl = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    async def authenticate_user(
        self, db: AsyncSession, login: str, password: str
    ):
        user = await self.user_repo.get_by_field(db, "login", login)
        if not user or not user.check_password(password):
            raise InvalidCredentialsError("Wrong login or password")
        return user

    async def login(
        self,
        db: AsyncSession,
        login: str,
        password: str,
        ip_address: str,
        user_agent: str,
    ):
        user = await self.authenticate_user(db, login, password)
        session_version = await self.session_service.get_session_version(
            str(user.id)
        )
        if not session_version:
            session_version = 1
            await self.session_service.set_session_version(
                str(user.id), session_version
            )
        access_token = self.jwt_service.create_access_token(
            user_id=str(user.id),
            session_version=session_version,
            role=user.role,
        )
        refresh_token = self.jwt_service.create_refresh_token(
            user_id=str(user.id),
            session_version=session_version,
            role=user.role,
        )

        await self.history_service.log_login(
            db,
            LoginHistoryCreate(
                user_id=str(user.id),
                ip_address=ip_address,
                user_agent=user_agent,
            ),
        )
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token
        )

    async def logout(self, refresh_token: str):
        if await self.session_service.is_refresh_token_invalid(refresh_token):
            raise InvalidSessionError("This refresh token is invalid.")
        ttl = int(self.refresh_ttl.total_seconds())
        await self.session_service.logout(refresh_token, ttl)

    async def logout_all(self, user_id: str):
        await self.session_service.logout_all(user_id)

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        if await self.session_service.is_refresh_token_invalid(refresh_token):
            raise InvalidSessionError("This refresh token is invalid.")
        decoded = self.jwt_service.validate_token_type(
            refresh_token, TokenTypes.REFRESH
        )
        user_id = decoded[PayloadKeys.USER]
        session_version = decoded[PayloadKeys.SESSION_VERSION]
        current_version = await self.session_service.get_session_version(
            user_id
        )
        role = decoded[PayloadKeys.ROLE]

        if current_version != session_version:
            raise InvalidSessionError("Session version mismatch.")

        ttl = int(self.refresh_ttl.total_seconds())
        await self.session_service.invalidate_refresh_token(refresh_token, ttl)
        return TokenResponse(
            access_token=self.jwt_service.create_access_token(
                user_id, current_version, role
            ),
            refresh_token=self.jwt_service.create_refresh_token(
                user_id, current_version, role
            ),
        )


async def get_auth_service(
    session_service: Annotated[SessionService, Depends(get_session_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    login_history_service: Annotated[
        LoginHistoryService, Depends(get_login_history_service)
    ],
) -> AuthService:
    user_repo = UserRepository()
    return AuthService(
        user_repo=user_repo,
        history_service=login_history_service,
        session_service=session_service,
        jwt_service=jwt_service,
    )
