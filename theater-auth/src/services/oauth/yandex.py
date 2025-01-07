import base64

import httpx
from core.config import settings

YANDEX_TOKEN_URL = "https://oauth.yandex.ru/token"
YANDEX_USER_INFO_URL = "https://login.yandex.ru/info"


async def exchange_code_for_tokens(code: str) -> dict:
    """Обмен кода авторизации на токены."""
    async with httpx.AsyncClient() as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.yandex_client_id,
            "client_secret": settings.yandex_client_secret,
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        response = await client.post(
            YANDEX_TOKEN_URL, data=data, headers=headers
        )
        response.raise_for_status()
        return response.json()


async def get_user_info(access_token: str) -> dict:
    """Получение информации о пользователе из Yandex."""
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": f"OAuth {access_token}"}
        response = await client.get(
            YANDEX_USER_INFO_URL, headers=headers, params={"format": "json"}
        )
        response.raise_for_status()
        return response.json()


async def revoke_token(access_token: str) -> None:
    """Отзыв токена Yandex."""
    async with httpx.AsyncClient() as client:
        data = {"access_token": access_token}
        auth_header = base64.b64encode(
            f"{settings.yandex_client_id}:{settings.yandex_client_secret}".encode()
        ).decode()
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {auth_header}",
        }
        response = await client.post(
            "https://oauth.yandex.ru/revoke_token", data=data, headers=headers
        )
        response.raise_for_status()
