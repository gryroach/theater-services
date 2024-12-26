from os import environ

from dotenv import load_dotenv
from split_settings.tools import include, optional

load_dotenv()

_ENV = environ.get('DJANGO_ENV') or 'development'

base_settings = [
    'components/common.py',
    'components/database.py',
    'components/installed_apps.py',
    'components/middlewares.py',
    'components/loggers.py',
    'components/tracer.py',
    # Select the right env:
    f'environments/{_ENV}.py',
    # Optionally override some settings:
    optional('environments/local.py'),
]

# Include settings:
include(*base_settings)
