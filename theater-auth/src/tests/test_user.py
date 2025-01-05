from uuid import UUID

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from models import User
from services.roles import Roles

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def create_admin_user(session: AsyncSession) -> User:
    """Создание админа"""
    user = User(
        login="admin",
        role=Roles.admin.name,
        password="123",
        first_name="Tester",
        last_name="Pass",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def create_regular_user(session: AsyncSession) -> User:
    """Создание пользователя"""
    user = User(
        login="testuser",
        role=Roles.regular_user.name,
        password="123",
        first_name="Tester",
        last_name="Pass",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture
async def login_admin_user(
    client: AsyncClient, create_admin_user: User
) -> dict:
    """Выполняет логин админа и возвращает токены доступа."""
    login_data = {
        "login": create_admin_user.login,
        "password": "123",
    }
    response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


@pytest_asyncio.fixture
async def login_user(client: AsyncClient, create_regular_user: User) -> dict:
    """Выполняет логин пользователя и возвращает токены доступа."""
    login_data = {
        "login": create_regular_user.login,
        "password": "123",
    }
    response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_200_OK
    return response.json()


async def test_login_user_wrong_pass(
    client: AsyncClient, create_regular_user: User
) -> None:
    """Тест неправильного пароля."""
    login_data = {
        "login": create_regular_user.login,
        "password": "wrong",
    }
    response = await client.post(
        "api-auth/v1/auth/login",
        json=login_data,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_user_role(
    client: AsyncClient, create_admin_user: User, login_admin_user: dict
) -> None:
    """
    Тест для получения роли пользователя
    """
    headers = {
        "Authorization": f"Bearer {login_admin_user['access_token']}",
        "X-Request-Id": "test",
    }
    response = await client.get(
        f"/api-auth/v1/users/{create_admin_user.id}/role",
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == Roles.admin.name
    assert data["permissions"] == Roles.admin.permissions.model_dump()


async def test_get_user_role_by_regular_user(
    client: AsyncClient, create_regular_user: User, login_user: dict
) -> None:
    """
    Тест для получения роли пользователя обычным пользователем
    """
    headers = {
        "Authorization": f"Bearer {login_user['access_token']}",
        "X-Request-Id": "test",
    }
    response = await client.get(
        f"/api-auth/v1/users/{create_regular_user.id}/role",
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_user_role_unauthorized(
    client: AsyncClient, create_admin_user: User
) -> None:
    """
    Тест авторизации при получении роли пользователя
    """
    response = await client.get(
        f"/api-auth/v1/users/{create_admin_user.id}/role",
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_set_user_role(
    client: AsyncClient, create_admin_user: User, login_admin_user: dict
) -> None:
    """
    Тест для обновления роли пользователя
    """
    new_role = {"role": "moderator"}
    headers = {
        "Authorization": f"Bearer {login_admin_user['access_token']}",
        "X-Request-Id": "test",
    }
    response = await client.patch(
        f"api-auth/v1/users/{create_admin_user.id}/role",
        json=new_role,
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "moderator"
    assert data["permissions"] == Roles.moderator.permissions.model_dump()


async def test_set_user_role_by_regular_user(
    client: AsyncClient, create_regular_user: User, login_user: dict
) -> None:
    """
    Тест для обновления роли пользователя обычным пользователем
    """
    new_role = {"role": "moderator"}
    headers = {
        "Authorization": f"Bearer {login_user['access_token']}",
        "X-Request-Id": "test",
    }
    response = await client.patch(
        f"api-auth/v1/users/{create_regular_user.id}/role",
        json=new_role,
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_set_user_role_unauthorized(
    client: AsyncClient, create_admin_user: User
) -> None:
    """
    Тест авторизации при обновлении роли пользователя
    """
    new_role = {"role": "moderator"}
    response = await client.patch(
        f"api-auth/v1/users/{create_admin_user.id}/role",
        json=new_role,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_user_role_not_found(
    client: AsyncClient, login_admin_user: dict
) -> None:
    """
    Тест для проверки ошибки при получении роли несуществующего пользователя
    """
    headers = {
        "Authorization": f"Bearer {login_admin_user['access_token']}",
        "X-Request-Id": "test",
    }
    non_existent_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    response = await client.get(
        f"api-auth/v1/users/{non_existent_user_id}/role",
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "User does not exists"


async def test_get_user_role_not_found_unauthorized(
    client: AsyncClient,
) -> None:
    """
    Тест авторизации при получении роли несуществующего пользователя
    """
    non_existent_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    response = await client.get(
        f"api-auth/v1/users/{non_existent_user_id}/role",
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_set_user_role_not_found(
    client: AsyncClient, login_admin_user: dict
) -> None:
    """
    Тест для проверки ошибки при обновлении роли несуществующего пользователя
    """
    headers = {
        "Authorization": f"Bearer {login_admin_user['access_token']}",
        "X-Request-Id": "test",
    }
    non_existent_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    new_role = {"role": "moderator"}
    response = await client.patch(
        f"api-auth/v1/users/{non_existent_user_id}/role",
        json=new_role,
        headers=headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert data["detail"] == "User does not exists"


async def test_set_user_role_not_found_unauthorized(
    client: AsyncClient,
) -> None:
    """
    Тест авторизации при обновлении роли несуществующего пользователя
    """
    non_existent_user_id = UUID("123e4567-e89b-12d3-a456-426614174000")
    new_role = {"role": "moderator"}
    response = await client.patch(
        f"api-auth/v1/users/{non_existent_user_id}/role",
        json=new_role,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_set_user_role_invalid(
    client: AsyncClient, create_admin_user: User, login_admin_user: dict
) -> None:
    """
    Тест для проверки ошибки при обновлении роли на несуществующую роль
    """
    headers = {
        "Authorization": f"Bearer {login_admin_user['access_token']}",
        "X-Request-Id": "test",
    }
    invalid_role = {"role": "invalid_role"}
    response = await client.patch(
        f"api-auth/v1/users/{create_admin_user.id}/role",
        json=invalid_role,
        headers=headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    data = response.json()
    assert "detail" in data
    assert data["detail"][0]["msg"] == "Value error, Role does not exists"


async def test_set_user_role_invalid_unauthorized(
    client: AsyncClient, create_admin_user: User
) -> None:
    """
    Тест авторизации при обновлении роли на несуществующую роль
    """
    invalid_role = {"role": "invalid_role"}
    response = await client.patch(
        f"api-auth/v1/users/{create_admin_user.id}/role",
        json=invalid_role,
        headers={"X-Request-Id": "test"},
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
