from enum import Enum

from config.services.auth_api_service import AuthAPIService
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()


class Roles(str, Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"


class CustomBackend(BaseBackend):
    def __init__(self):
        self.auth_service = AuthAPIService(base_url=settings.AUTH_API_BASE_URL)

    def authenticate(self, request, username=None, password=None):
        request_id = request.headers.get("X-Request-Id", "unknown-request-id")

        auth_data = self.auth_service.authenticate_user(
            request_id=request_id, login=username, password=password
        )
        if not auth_data:
            return None

        access_token = auth_data.get("access_token")
        if not access_token:
            return None

        user_data = self.auth_service.get_user_info(
            request_id=request_id, access_token=access_token
        )
        if not user_data:
            return None

        return self._get_or_create_user(user_data)

    def _get_or_create_user(self, data: dict):
        """
        Создает или обновляет пользователя на основе данных из внешнего API.

        :param data: Данные пользователя
        :return: Экземпляр пользователя
        """
        role = data.get("role")
        if role not in {Roles.ADMIN.value, Roles.MODERATOR.value}:
            return None

        user, created = User.objects.get_or_create(login=data["login"])
        user.login = data.get("login")
        user.first_name = data.get("first_name")
        user.last_name = data.get("last_name")
        user.is_admin = role == Roles.ADMIN.value
        user.is_moderator = role == Roles.MODERATOR.value
        user.is_staff = user.is_admin or user.is_moderator
        user.is_active = data.get("is_active", True)
        user.save()
        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
