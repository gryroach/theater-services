import base64
from abc import ABC, abstractmethod
from typing import Dict

import httpx
from google.auth.transport import requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow

from core.config import settings
from exceptions.auth_exceptions import AuthError


class OAuthProvider(ABC):
    """
    Интерфейс для OAuth-провайдеров.
    """

    @abstractmethod
    def get_authorization_url(self, state: str = "") -> str:
        """
        Получение url для редиректа в сервис провайдера.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_user_info(self, url: str, code: str) -> Dict[str, str]:
        """
        Получение информации о пользователе.
        """
        raise NotImplementedError

    @abstractmethod
    async def exchange_code_for_tokens(self, code: str | None = None, url: str | None = None) -> dict[str, str]:
        """
        Обмен кода авторизации на токены. Возможна реализация с парсингом url, либо напрямую через полученный код.
        """
        raise NotImplementedError

    @abstractmethod
    async def revoke_tokens(self, access_token: str) -> None:
        """
        Отзыв токенов.
        """
        raise NotImplementedError


class GoogleOAuthProvider(OAuthProvider):
    def __init__(self) -> None:
        self.flow = Flow.from_client_secrets_file(
            settings.google_client_file_path,
            scopes=[
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
                "openid",
            ],
        )
        self.flow.redirect_uri = (
            f"https://{settings.google_redirect_host}/api-auth/v1/oauth/google/callback"
        )

    def get_authorization_url(self, state: str = "") -> str:
        authorization_url, _ = self.flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            state=state,
        )
        return authorization_url

    async def get_user_info(self, url: str, code: str) -> Dict[str, str]:
        """
        Получение информации о пользователе.
        """
        try:
            await self.exchange_code_for_tokens(url=url)
            user_info = id_token.verify_oauth2_token(
                self.flow.credentials.id_token,
                requests.Request(),
                settings.google_client_id,
            )
            user_info["first_name"] = user_info.get("given_name", "")
            user_info["last_name"] = user_info.get("family_name", "")
            return user_info
        except Exception as e:
            raise AuthError(f"Google OAuth error: {e}")

    async def revoke_tokens(self, access_token: str) -> None:
        """
        Отзыв токенов через Google API.
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://accounts.google.com/o/oauth2/revoke",
                    params={"token": access_token},
                    headers={
                        "content-type": "application/x-www-form-urlencoded"
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as e:
            raise AuthError(f"Google token revoke failed: {e}")

    async def exchange_code_for_tokens(self, code: str | None = None, url: str | None = None) -> dict[str, str]:
        """
        Обмен кода авторизации на токены.
        """
        return self.flow.fetch_token(authorization_response=url)


class YandexOAuthProvider(OAuthProvider):
    def get_authorization_url(self, state: str = "") -> str:
        return (
            f"https://oauth.yandex.ru/authorize?"
            f"response_type=code&"
            f"client_id={settings.yandex_client_id}&"
            f"state={state}&"
            f"redirect_uri=https://{settings.yandex_redirect_host}/api-auth/v1/oauth/yandex/callback"
        )

    async def exchange_code_for_tokens(self, code: str | None = None, url: str | None = None) -> dict[str, str]:
        """
        Обмен кода авторизации на токены.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth.yandex.ru/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.yandex_client_id,
                    "client_secret": settings.yandex_client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            return response.json()

    async def get_user_info(self, url: str, code: str) -> Dict[str, str]:
        """
        Получение информации о пользователе.
        """
        tokens = await self.exchange_code_for_tokens(code=code)
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://login.yandex.ru/info",
                headers={"Authorization": f"OAuth {tokens['access_token']}"},
                params={"format": "json"},
            )
            response.raise_for_status()
            return response.json()

    async def revoke_tokens(self, access_token: str) -> None:
        """
        Отзыв токенов через Yandex API.
        """
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
                "https://oauth.yandex.ru/revoke_token",
                data=data,
                headers=headers,
            )
            response.raise_for_status()


def get_oauth_provider(provider_name: str) -> OAuthProvider:
    if provider_name not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider_name}")
    return PROVIDERS[provider_name][0]


PROVIDERS: dict[str, tuple[OAuthProvider, str]] = {
    "google": (GoogleOAuthProvider(), "google_id"),
    "yandex": (YandexOAuthProvider(), "yandex_id"),
}
