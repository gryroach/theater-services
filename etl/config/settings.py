import os

from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

POLL_INTERVAL = 10

FIRST_TIME_STARTED = False

# Параметры для backoff
MAX_BACKOFF = 60  # максимальное время ожидания в секундах
BASE_BACKOFF = 5  # базовое время ожидания между попытками в секундах
MAX_RETRIES = 5  # максимальное количество попыток

# Конфигурация для PostgreSQL
POSTGRES_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "options": os.getenv("DB_OPTIONS", ""),
}

# Конфигурация для Elasticsearch
ES_CONFIG = {
    "hosts": "{}{}:{}".format(
        os.getenv("ELASTIC_SCHEMA", "http://"),
        os.getenv("ES_HOST", "elasticsearch"),
        os.getenv("ES_PORT", "9200"),
    ),
    "verify_certs": os.getenv("ES_VERIFY_CERTS", "false").lower() == "true",
    "retry_on_timeout": False,
    "max_retries": 1,
}

# Конфигурация для Redis
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "redis"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": int(os.getenv("REDIS_DB", 0)),
    "password": os.getenv("REDIS_PASSWORD", None),
}

# Схемы для ES
common_analysis_settings = {
    "filter": {
        "english_stop": {"type": "stop", "stopwords": "_english_"},
        "english_stemmer": {"type": "stemmer", "language": "english"},
        "english_possessive_stemmer": {
            "type": "stemmer",
            "language": "possessive_english",
        },
        "russian_stop": {"type": "stop", "stopwords": "_russian_"},
        "russian_stemmer": {"type": "stemmer", "language": "russian"},
    },
    "analyzer": {
        "ru_en": {
            "tokenizer": "standard",
            "filter": [
                "lowercase",
                "english_stop",
                "english_stemmer",
                "english_possessive_stemmer",
                "russian_stop",
                "russian_stemmer",
            ],
        }
    },
}
movies_schema = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": common_analysis_settings,
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "imdb_rating": {"type": "float"},
            "genres": {"type": "keyword"},
            "title": {
                "type": "text",
                "analyzer": "ru_en",
                "fields": {"raw": {"type": "keyword"}},
            },
            "description": {"type": "text", "analyzer": "ru_en"},
            "directors_names": {"type": "text", "analyzer": "ru_en"},
            "actors_names": {"type": "text", "analyzer": "ru_en"},
            "writers_names": {"type": "text", "analyzer": "ru_en"},
            "genres_details": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "directors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "actors": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
            "writers": {
                "type": "nested",
                "dynamic": "strict",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text", "analyzer": "ru_en"},
                },
            },
        },
    },
}
genres_schema = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": common_analysis_settings,
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "name": {"type": "text", "analyzer": "ru_en"},
            "description": {"type": "text", "analyzer": "ru_en"},
        },
    },
}
persons_schema = {
    "settings": {
        "refresh_interval": "1s",
        "analysis": common_analysis_settings,
    },
    "mappings": {
        "dynamic": "strict",
        "properties": {
            "id": {"type": "keyword"},
            "full_name": {"type": "text", "analyzer": "ru_en"},
            "roles": {"type": "keyword"},
            "films": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "title": {"type": "text", "analyzer": "ru_en"},
                    "imdb_rating": {"type": "float"},
                },
            },
        },
    },
}
