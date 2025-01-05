import logging

import requests

logger = logging.getLogger(__name__)


class AuthAPIService:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def authenticate_user(
        self, request_id: str, login: str, password: str
    ) -> dict | None:
        """
        Отправляет запрос на аутентификацию в внешний сервис.

        :param request_id: ID запроса (X-Request-Id)
        :param login: Логин пользователя
        :param password: Пароль пользователя
        :return: Токены, если запрос успешен, иначе None
        """
        url = f"{self.base_url}/auth/login"
        self.session.headers.update({"X-Request-Id": request_id})

        payload = {"login": login, "password": password}
        try:
            response = self.session.post(url, json=payload)
            if response.status_code == requests.codes.ok:
                return response.json()
        except requests.RequestException as e:
            logger.error(f"Error during authentication request: {e}")
        return None

    def get_user_info(self, request_id: str, access_token: str) -> dict | None:
        """
        Получает информацию о пользователе из сервиса авторизации.

        :param request_id: ID запроса (X-Request-Id)
        :param access_token: Токен доступа пользователя
        :return: Данные пользователя, если запрос успешен, иначе None
        """
        url = f"{self.base_url}/profile/info"
        self.session.headers.update(
            {
                "X-Request-Id": request_id,
                "Authorization": f"Bearer {access_token}",
            }
        )

        try:
            response = self.session.get(url)
            if response.status_code == requests.codes.ok:
                return response.json()
            logger.error(
                f"Failed to fetch user info: {response.status_code} {response.text}"
            )
        except requests.RequestException as e:
            logger.error(f"Error during user info request: {e}")
        return None
