import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from models import User
from services.roles import Roles

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def create_user(session: AsyncSession) -> User:
    """Создание пользователя."""
    user = User(
        login="testuser",
        role=Roles.admin.name,
        password="123",
        first_name="Tester",
        last_name="Pass",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def test_login(client: AsyncClient, create_user: User) -> None:
    """
    Тест логина пользователя.
    """
    login_data = {
        "login": create_user.login,
        "password": "123",
    }
    response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_200_OK
    tokens = response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """
    Тест логина с неверными данными.
    """
    login_data = {
        "login": "wronguser",
        "password": "wrongpass",
    }
    response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json().get("detail") == "Wrong login or password"


async def test_refresh_token_invalid(client: AsyncClient) -> None:
    """
    Тест обновления access токена с неверным refresh токеном.
    """
    invalid_refresh_token = "invalidtoken"
    response = await client.post(
        "api-auth/v1/auth/refresh",
        json={"refresh_token": invalid_refresh_token},
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json().get("detail") == "Token is invalid."


async def test_logout(client: AsyncClient, create_user: User) -> None:
    """
    Тест выхода из системы (logout).
    """
    login_data = {
        "login": create_user.login,
        "password": "123",
    }
    login_response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    logout_response = await client.post(
        "api-auth/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Request-Id": "test",
        },
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_response.status_code == status.HTTP_200_OK

    # Проверка недействительности refresh токена
    protected_response = await client.post(
        "/api-auth/v1/auth/refresh",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Request-Id": "test",
        },
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert protected_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        protected_response.json().get("detail")
        == "This refresh token is invalid."
    )


async def test_logout_all(client: AsyncClient, create_user: User) -> None:
    """
    Тест выхода из всех сессий (logout all).
    """
    login_data = {
        "login": create_user.login,
        "password": "123",
    }
    login_response_1 = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert login_response_1.status_code == status.HTTP_200_OK
    tokens_1 = login_response_1.json()

    login_response_2 = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert login_response_2.status_code == status.HTTP_200_OK
    tokens_2 = login_response_2.json()

    # Проверка валидности токенов
    for token in [tokens_1["access_token"], tokens_2["access_token"]]:
        protected_response = await client.get(
            "/api-auth/v1/auth/login-history",
            headers={
                "Authorization": f"Bearer {token}",
                 "X-Request-Id": "test",
            },
        )
        assert protected_response.status_code == status.HTTP_200_OK

    # Выход из всех сессий
    logout_all_response = await client.post(
        "api-auth/v1/auth/logout/all",
        headers={
            "Authorization": f"Bearer {tokens_1['access_token']}",
            "X-Request-Id": "test",
        },
    )
    assert logout_all_response.status_code == status.HTTP_200_OK

    # Проверка недействительности обоих токенов
    for token in [tokens_1["access_token"], tokens_2["access_token"]]:
        protected_response = await client.get(
            "/api-auth/v1/auth/login-history",
            headers={
                "Authorization": f"Bearer {token}",
                 "X-Request-Id": "test",
            },
        )
        assert protected_response.status_code == status.HTTP_401_UNAUTHORIZED
        assert (
            protected_response.json().get("detail")
            == "Session is invalid or expired"
        )


async def test_refresh_token(client: AsyncClient, create_user: User) -> None:
    """
    Тест обновления access токена.
    """
    # Регистрируемся срабатывания бизнес логики установки версии сессии
    user_data = {
        "login": "string",
        "password": "string",
        "first_name": "string",
        "last_name": "string",
        "role": "regular_user",
    }
    _ = await client.post(
        "api-auth/v1/auth/signup",
        json=user_data,
        headers={"X-Request-Id": "test"},
    )
    login_data = {
        "login": user_data["login"],
        "password": user_data["password"],
    }
    login_response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert login_response.status_code == status.HTTP_200_OK
    tokens = login_response.json()
    refresh_response = await client.post(
        "api-auth/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"X-Request-Id": "test"},
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    refreshed_tokens = refresh_response.json()
    assert "access_token" in refreshed_tokens
