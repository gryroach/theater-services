from datetime import datetime, timedelta, timezone

import jwt

from core.config import settings
from core.enums import PayloadKeys, TokenTypes
from exceptions.auth_exceptions import (
    InvalidAlgorithmError,
    InvalidSessionError,
    InvalidTokenError,
)


class JWTService:
    def __init__(self):
        with open(settings.private_key, "r") as private_key_file:
            self.private_key = private_key_file.read()
        with open(settings.public_key, "r") as public_key_file:
            self.public_key = public_key_file.read()
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire = timedelta(
            days=settings.ACCESS_TOKEN_EXPIRE_DAYS
        )
        self.refresh_token_expire = timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    def _create_token(self, payload: dict) -> str:
        """Создает JWT-токен с подписью приватным ключом (асимметричный)."""
        return jwt.encode(payload, self.private_key, algorithm=self.algorithm)

    def create_access_token(
            self, user_id: str, session_version: int, role: str
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            PayloadKeys.USER: user_id,
            PayloadKeys.SESSION_VERSION: session_version,
            PayloadKeys.IAT: now,
            PayloadKeys.EXP: now + self.access_token_expire,
            PayloadKeys.TYPE: TokenTypes.ACCESS,
            PayloadKeys.ROLE: role,
        }
        return self._create_token(payload)

    def create_refresh_token(
            self, user_id: str, session_version: int, role: str
    ) -> str:
        now = datetime.now(timezone.utc)
        payload = {
            PayloadKeys.USER: user_id,
            PayloadKeys.SESSION_VERSION: session_version,
            PayloadKeys.IAT: now,
            PayloadKeys.EXP: now + self.refresh_token_expire,
            PayloadKeys.TYPE: TokenTypes.REFRESH,
            PayloadKeys.ROLE: role,
        }
        return self._create_token(payload)

    def decode_token(self, token: str) -> dict:
        """
        Декодирует JWT-токен с использованием публичного ключа (асимметричный).
        """
        try:
            decoded = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                verify=True,
            )
            return decoded
        except jwt.exceptions.InvalidAlgorithmError:
            raise InvalidAlgorithmError(
                "The specified alg value is not allowed."
            )
        except jwt.ExpiredSignatureError:
            raise InvalidTokenError("Token has expired.")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Token is invalid.")

    def validate_token_type(self, token: str, expected_type: str) -> dict:
        """Проверяет, что токен имеет ожидаемый тип (access/refresh)."""
        decoded = self.decode_token(token)
        if decoded.get(PayloadKeys.TYPE) != expected_type:
            raise InvalidTokenError(f"Token type must be '{expected_type}'.")
        return decoded

    def validate_user_and_version(
        self, token: str, user_id: str, session_version: int
    ) -> dict:
        """
        Проверяет, что user_id и версия сессии в токене совпадают с ожидаемыми.
        """
        decoded = self.decode_token(token)
        if decoded.get(PayloadKeys.USER) != user_id:
            raise InvalidTokenError("Token user mismatch.")
        if decoded.get(PayloadKeys.SESSION_VERSION) != session_version:
            raise InvalidSessionError("Session version mismatch.")
        return decoded


def get_jwt_service() -> JWTService:
    """Создает экземпляр сервиса JWT."""
    return JWTService()
