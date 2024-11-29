import logging

import backoff
from elasticsearch import Elasticsearch
from functional.settings import test_settings

logging.getLogger(__name__)


@backoff.on_exception(backoff.expo, ConnectionError, max_tries=10)
def is_es_available() -> bool:
    """Проверяет доступность Elasticsearch."""
    es_client = Elasticsearch(
        hosts=test_settings.elasticsearch_url, verify_certs=False
    )
    if es_client.ping():
        logging.info("Соединение с ES установленно")
    else:
        raise ConnectionError


if __name__ == "__main__":
    is_es_available()
