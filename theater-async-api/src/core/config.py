import os
from logging import config as logging_config

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
<<<<<<< HEAD
PROJECT_NAME = os.getenv('PROJECT_NAME', 'movies')
=======
PROJECT_NAME = os.getenv('PROJECT_NAME', 'Read-only API для онлайн-кинотеатра')
>>>>>>> main

# Настройки Redis
REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Настройки Elasticsearch
<<<<<<< HEAD
ELASTIC_HOST = os.getenv('ELASTIC_HOST', '127.0.0.1')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))
=======
ELASTIC_HOST = os.getenv('ES_HOST', '127.0.0.1')
ELASTIC_PORT = int(os.getenv('ES_PORT', 9200))
ELASTIC_SCHEMA = os.getenv('ELASTIC_SCHEMA', 'http://')
>>>>>>> main

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
