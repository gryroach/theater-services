import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY")

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "users.User"

AUTH_API_BASE_URL = os.getenv(
    "AUTH_API_BASE_URL", "http://localhost:8000/api-auth/v1"
)

AUTHENTICATION_BACKENDS = [
    "users.backends.CustomBackend",
    # 'django.contrib.auth.backends.ModelBackend',
]

REST_FRAMEWORK = {
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
}

LANGUAGE_CODE = "ru-RU"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = "static"

MEDIA_URL = "media/"
MEDIA_ROOT = "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOCALE_PATHS = ["movies/locale"]

INTERNAL_IPS = [
    "127.0.0.1",
]
