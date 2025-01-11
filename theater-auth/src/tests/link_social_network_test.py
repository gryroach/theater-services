"""
Скрипт для тестирования привязки социальной сети к аккаунту
"""

import webbrowser

import requests

# Bearer токен
TOKEN = "your_token"

# URL для запроса
# URL = 'https://127.0.0.1/api-auth/v1/oauth/google/link'
URL = "https://127.0.0.1/api-auth/v1/oauth/yandex/link"


def make_request():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    response = requests.get(
        URL, headers=headers, allow_redirects=False, verify=False
    )

    if response.status_code in (301, 302, 307):
        redirect_url = response.headers["Location"]
        print(f"Redirecting to: {redirect_url}")
        webbrowser.open(redirect_url)
    else:
        print(f"Response: {response.text}")


if __name__ == "__main__":
    make_request()
