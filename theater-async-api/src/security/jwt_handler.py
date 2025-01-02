import jwt
from core.config import settings


def decode_token(token: str) -> dict:
    """
    Декодирует токен JWT, возвращая полезную нагрузку в виде словаря.
    """
    try:
        return jwt.decode(
            token, settings.jwt_public_key, algorithms=[settings.jwt_algorithm]
        )
    except Exception:
        return None
