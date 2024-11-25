import logging
from typing import Any

logger = logging.getLogger(__name__)


async def write_data_to_es(
    es_write_data: Any,
    es_data: list[dict],
    index_settings: Any,
) -> None:
    """
    Записывает данные в Elasticsearch.

    Args:
        es_write_data (Any): Фикстура для записи данных.
        es_data (list[dict]): Данные для записи.
        index_settings (Any): Настройки индекса.
    """
    try:
        await es_write_data(es_data, index_settings.es_index)
        logger.info("Data successfully written to Elasticsearch.")
    except Exception as e:
        logger.error(f"Failed to write data to Elasticsearch: {e}")
        raise
