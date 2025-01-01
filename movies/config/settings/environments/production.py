from config.settings.components.common import ALLOWED_HOSTS

DEBUG = False

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

ALLOWED_HOSTS += [
    'admin'
]
