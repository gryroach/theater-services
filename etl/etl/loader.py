import logging
from typing import Any

import backoff
from config.settings import MAX_BACKOFF, MAX_RETRIES
from elasticsearch import Elasticsearch, helpers


class EsLoaderBulkError(Exception):
    """Ошибка при создании/обновлении документа."""

    pass


class EsLoaderDocumentError(Exception):
    """Ошибка при использовании helpers.bulk."""

    pass


class Loader:
    def __init__(self, es: Elasticsearch):
        self.es = es

    def create_index(self, index_name: str, schema: dict[str, Any]) -> None:
        """Создает индекс в Elasticsearch, если он не существует."""
        try:
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=schema)
                logging.info(
                    f"Индекс '{index_name}' создан с заданной схемой."
                )
            else:
                logging.info(f"Индекс '{index_name}' уже существует.")
        except Exception as e:
            logging.error(
                f"Ошибка при создании индекса '{index_name}': {e}",
                exc_info=True,
            )

    @backoff.on_exception(
        backoff.expo,
        (EsLoaderBulkError, EsLoaderDocumentError),
        max_time=MAX_BACKOFF,
        max_tries=MAX_RETRIES,
        jitter=backoff.random_jitter,
    )
    def load_data(self, index_name: str, data: list[dict[str, Any]]) -> None:
        """Загружает данные в указанный индекс Elasticsearch."""
        actions = []
        for record in data:
            action = {
                "_index": index_name,
                "_id": record["id"],
                "_source": record,
            }
            actions.append(action)

        if actions:
            try:
                success, _ = helpers.bulk(self.es, actions)
                logging.info(f"Успешно индексировано {success} документов.")
            except Exception as e:
                logging.error(
                    f"Не удалось индексировать документы: {e}", exc_info=True
                )
                for error in e.errors:
                    logging.error(error, exc_info=True)
                raise EsLoaderBulkError(e)

    def index_exists(self, index_name: str) -> bool:
        """Проверяет существование индекса в Elasticsearch."""
        return self.es.indices.exists(index=index_name)

    def delete_index(self, index_name: str) -> bool | None:
        """Удаляет индекс в Elasticsearch, если он существует."""
        try:
            if self.index_exists(index_name):
                self.es.indices.delete(index=index_name)
                logging.info(f"Индекс '{index_name}' успешно удалён.")
                return True
            else:
                logging.warning(
                    f"Индекс '{index_name}' не существует, не может быть удалён."
                )
                return False
        except Exception as e:
            logging.error(
                f"Ошибка при удалении индекса '{index_name}': {e}",
                exc_info=True,
            )
            return False
