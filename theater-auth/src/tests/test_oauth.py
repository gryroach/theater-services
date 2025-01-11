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
        if url.startswith("https://oauth2.googleapis.com/token"):
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
                    "access_token": "test_google_access_token",
                    "expires_in": 3600,
                    "id_token": "test_google_id_token",
                    "token_type": "Bearer",
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
        if url.startswith("https://www.googleapis.com/oauth2/v3/userinfo"):
            return Response(
                status_code=200,
                request=Request(
                    method="GET",
                    url=url,
                    headers=kwargs.get("headers", {}),
                ),
                json={
                    "sub": "google_user_id",
                    "email": "test_user@gmail.com",
                    "given_name": "Google",
                    "family_name": "User",
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


@pytest.fixture
def mock_secure_transport(mocker):
    mocker.patch(
        "oauthlib.oauth2.rfc6749.parameters.is_secure_transport",
        return_value=True,
    )


@pytest.fixture
def mock_jwt_bearer(mocker):
    mocker.patch(
        "dependencies.auth.JWTBearer.__call__",
        new=AsyncMock(return_value=True),
    )


async def test_yandex_exchange_tokens_success(
    mock_post,
    mock_user_repository,
    mock_auth_service,
    mock_jwt_bearer,
    mock_secure_transport,
):
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/yandex/exchange-tokens",
            headers={"X-Request-Id": "test_oauth"},
            params={"code": "test_code"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["oauth_tokens"]["access_token"] == "test_oauth_access_token"
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


async def test_google_exchange_tokens_success(
    mock_post,
    mock_get,
    mock_user_repository,
    mock_auth_service,
    mock_jwt_bearer,
    mock_secure_transport,
    mocker,
):
    mocker.patch(
        "services.oauth.GoogleOAuthProvider.exchange_code_for_tokens",
        new=AsyncMock(
            return_value={
                "access_token": "test_google_access_token",
                "refresh_token": "test_google_refresh_token",
                "expires_in": 3600,
            }
        ),
    )

    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/google/exchange-tokens?code=test_code",
            headers={"X-Request-Id": "test_google"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["oauth_tokens"]["access_token"] == "test_google_access_token"


async def test_yandex_exchange_tokens_failure():
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/yandex/exchange-tokens",
            headers={"X-Request-Id": "test_oauth"},
            params={"code": "invalid_code"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"


async def test_google_exchange_tokens_failure():
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/google/exchange-tokens",
            headers={"X-Request-Id": "test_google"},
            params={"code": "invalid_code"},
        )
    assert response.status_code == 403
    assert response.json()["detail"] == "Not authenticated"


async def test_yandex_revoke_tokens_success(mocker):
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


async def test_google_revoke_tokens_success(mocker):
    mocker.patch(
        "services.oauth.GoogleOAuthProvider.revoke_tokens",
        new=AsyncMock(return_value=None),
    )
    with TestClient(app) as sync_client:
        response = sync_client.post(
            "/api-auth/v1/oauth/google/revoke-tokens",
            headers={"X-Request-Id": "test_google"},
            params={"access_token": "test_access_token"},
        )

    assert response.status_code == 200
    assert (
        response.json()["detail"]
        == "Tokens for provider 'google' successfully revoked."
    )
