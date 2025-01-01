from typing import Annotated, Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from db.db import get_session
from exceptions.auth_exceptions import InvalidTokenError, TokenExpiredError
from exceptions.user_exceptions import UserDoesNotExistsError, UserError
from schemas.jwt import JwtTokenPayload
from schemas.user import UserInDB
from services.jwt_service import JWTService, get_jwt_service
from services.session_service import SessionService, get_session_service
from services.user import UserService, get_user_service


class JWTBearer(HTTPBearer):
    def __init__(
        self,
        auto_error: bool = True,
    ):
        super().__init__(auto_error=auto_error)
        self.jwt_service: JWTService | None = None
        self.session_service: SessionService | None = None
        self.token_payload: JwtTokenPayload | None = None

    async def __call__(
        self,
        request: Request,
        jwt_service: JWTService = Depends(get_jwt_service),
        session_service: SessionService = Depends(get_session_service),
    ) -> JwtTokenPayload:
        self.jwt_service = jwt_service
        self.session_service = session_service
        credentials: HTTPAuthorizationCredentials = await super().__call__(
            request
        )
        await self.verify_jwt(credentials.credentials)
        return self.token_payload

    async def verify_jwt(self, token: str) -> None:
        try:
            self.token_payload = JwtTokenPayload(
                **self.jwt_service.decode_token(token)
            )
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")

        current_version = await self.session_service.get_session_version(
            self.token_payload.user
        )

        if not current_version or int(current_version) != int(
            self.token_payload.session_version
        ):
            raise InvalidTokenError("Session is invalid or expired")


async def get_current_user(
    token_payload: Annotated[JwtTokenPayload, Depends(JWTBearer())],
    user_service: Annotated[UserService, Depends(get_user_service)],
    db: Annotated[AsyncSession, Depends(get_session)],
) -> UserInDB:
    try:
        user_id = UUID(token_payload.user)
    except ValueError:
        raise UserError("Invalid user id")
    user = await user_service.user_repo.get(db, user_id)
    if not user:
        raise UserDoesNotExistsError("User not found")
    return UserInDB.model_validate(user)


def require_roles(
        required_roles: list[str]
) -> Callable[[JwtTokenPayload], JwtTokenPayload]:
    def dependency(
        token_payload: Annotated[JwtTokenPayload, Depends(JWTBearer())]
    ) -> JwtTokenPayload:
        if token_payload.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return token_payload

    return dependency
