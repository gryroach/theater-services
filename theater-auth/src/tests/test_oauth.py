from unittest.mock import AsyncMock

import pytest
from core.config import settings
from fastapi.testclient import TestClient
from httpx import Request, Response
from main import app
from models import User
from schemas.refresh import TokenResponse
from services.roles import Roles

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_post(mocker):
    async def post_side_effect(url, *args, **kwargs):
        if url == "https://oauth.yandex.ru/token":
            return Response(
                status_code=200,
                request=Request(
                    method="POST",
                    url=url,
                    headers={
                        "Content-Type": "application/x-www-form-urlencoded"
                    },
                ),
                json={
                    "access_token": "test_oauth_access_token",
                    "expires_in": 31268652,
                    "refresh_token": "test_oauth_refresh_token",
                    "token_type": "bearer",
                },
            )
        return Response(
            status_code=404,
            request=Request(method="POST", url=url),
            json={"error": "Not Found"},
        )

    return mocker.patch(
        "httpx.AsyncClient.post", new=AsyncMock(side_effect=post_side_effect)
    )


@pytest.fixture
def mock_get(mocker):
    async def get_side_effect(url, *args, **kwargs):
        if url == "https://login.yandex.ru/info":
            return Response(
                status_code=200,
                request=Request(
                    method="GET",
                    url=url,
                    headers=kwargs.get("headers", {}),
                ),
                json={
                    "id": "123456789",
                    "login": "test_user@yandex.ru",
                    "first_name": "Test",
                    "last_name": "User",
                },
            )
        return Response(
            status_code=404,
            request=Request(method="GET", url=url),
            json={"error": "Not Found"},
        )

    return mocker.patch(
        "httpx.AsyncClient.get", new=AsyncMock(side_effect=get_side_effect)
    )


@pytest.fixture
def mock_user_repository(mocker):
    mocker.patch(
        "repositories.user.UserRepository.get_by_field",
        new=AsyncMock(
            return_value=User(
                login="test_user@yandex.ru",
                role=Roles.admin.name,
                password="123",
                first_name="Tester",
                last_name="Pass",
            )
        ),
    )


@pytest.fixture
def mock_auth_service(mocker):
    return mocker.patch(
        "services.auth.AuthService.login",
        new=AsyncMock(
            return_value=TokenResponse(
                access_token="jwt_access_token",
                refresh_token="jwt_refresh_token",
            )
        ),
    )


async def test_exchange_tokens_success(
    mock_post, mock_get, mock_user_repository, mock_auth_service, mocker
):
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/yandex/exchange-tokens",
            headers={"X-Request-Id": "test_oauth"},
            json={"code": "test_code"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["oauth_tokens"]["access_token"] == "test_oauth_access_token"
    assert data["auth_tokens"]["access_token"] == "jwt_access_token"

    mock_post.assert_awaited_once_with(
        "https://oauth.yandex.ru/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "code": "test_code",
            "grant_type": "authorization_code",
            "client_id": settings.yandex_client_id,
            "client_secret": settings.yandex_client_secret,
        },
    )
    mock_get.assert_awaited_once_with(
        "https://login.yandex.ru/info",
        headers={"Authorization": "OAuth test_oauth_access_token"},
        params={
            "format": "json",
        },
    )


async def test_exchange_tokens_failure():
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/yandex/exchange-tokens",
            headers={"X-Request-Id": "test_oauth"},
            json={"code": "invalid_code"},
        )
    assert response.status_code == 403
    assert (
        response.json()["detail"]
        == "Token exchange failed: Client error '400 Bad Request' for url"
        " 'https://oauth.yandex.ru/token'\nFor more information check:"
        " https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/400"
    )


async def test_revoke_tokens_success(mocker):
    mocker.patch(
        "services.oauth.YandexOAuthProvider.revoke_tokens",
        new=AsyncMock(return_value=None),
    )
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/yandex/revoke-tokens",
            headers={"X-Request-Id": "test_oauth"},
            params={"access_token": "test_access_token"},
        )

    assert response.status_code == 200
    assert (
        response.json()["detail"]
        == "Tokens for provider 'yandex' successfully revoked."
    )
