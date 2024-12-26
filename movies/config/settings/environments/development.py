import os

from config.settings.components.common import ALLOWED_HOSTS
from config.settings.components.installed_apps import INSTALLED_APPS
from config.settings.components.loggers import LOGGING
from config.settings.components.middlewares import MIDDLEWARE

DEBUG = True

ALLOWED_HOSTS += [
    'localhost',
    '0.0.0.0',
    '127.0.0.1',
    '[::1]',
    'admin'
]

INSTALLED_APPS += (
    'debug_toolbar',
)
MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    *MIDDLEWARE,
]

if os.getenv('LOG_SQL') == 'True':
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['debug-console'],
        'propagate': False,
    }

CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:8080",]
