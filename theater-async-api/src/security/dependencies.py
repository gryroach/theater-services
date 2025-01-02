import http
import logging

from fastapi import HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_handler import decode_token

logger = logging.getLogger(__name__)


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        """
        Проверяет токен, выполняет graceful degradation при ошибках.
        """
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(
                request
            )
            if not credentials or credentials.scheme != "Bearer":
                logger.warning(
                    "Token absent or invalid. Assigning 'regular_user'."
                )
                return {
                    "role": "regular_user",
                    "error": "Missing or invalid token",
                }

            decoded_token = self.parse_token(credentials.credentials)
            if not decoded_token:
                logger.warning(
                    "Token expired or invalid. Assigning 'regular_user'."
                )
                return {
                    "role": "regular_user",
                    "error": "Invalid or expired token",
                }

            return decoded_token
        except Exception as e:
            logger.error(
                f"Authorization service failure: {e}. Assigning 'regular_user'."
            )
            return {
                "role": "regular_user",
                "error": "Authorization service failure",
            }

    @staticmethod
    def parse_token(jwt_token: str) -> dict:
        """
        Декодирует токен. Возвращает None, если токен невалиден.
        """
        try:
            return decode_token(jwt_token)
        except Exception as e:
            logger.error(f"Token decoding failed: {e}")
            return None


security_jwt = JWTBearer()
