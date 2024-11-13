import logging
from datetime import datetime

import redis

logger = logging.getLogger(__name__)


class RedisStateManager:
    def __init__(self, config: dict):
        """
        Инициализация клиента Redis.

        :param config: Конфигурация для подключения к Redis.
        """
        self.redis_client = redis.Redis(**config)
        logger.info("Redis client initialized with config: %s", config)

    def get_last_modified(self, table_name: str) -> str | None:
        """
        Получить время последнего изменения для заданной таблицы.

        :param table_name: Название таблицы.
        :return: Время последнего изменения в ISO формате или None, если не найдено.
        """
        try:
            last_modified = self.redis_client.get(
                f"{table_name}_last_modified"
            )
            result = last_modified.decode("utf-8") if last_modified else None
            logger.debug(
                "Retrieved last_modified for %s: %s", table_name, result
            )
            return result
        except Exception as e:
            logger.error(
                "Error retrieving last_modified for %s: %s", table_name, e
            )
            return None

    def set_last_modified(self, table_name: str, timestamp: datetime):
        """
        Установить время последнего изменения для заданной таблицы.

        :param table_name: Название таблицы.
        :param timestamp: Время последнего изменения.
        """
        if not isinstance(timestamp, datetime):
            logger.error(
                "Invalid timestamp: %s. Must be a datetime instance.",
                timestamp,
            )
            raise ValueError("Timestamp must be a datetime instance.")

        timestamp_iso = timestamp.isoformat()
        try:
            self.redis_client.set(f"{table_name}_last_modified", timestamp_iso)
            logger.debug(
                "Set last_modified for %s: %s", table_name, timestamp_iso
            )
        except Exception as e:
            logger.error(
                "Error setting last_modified for %s: %s", table_name, e
            )

    def set_process_flag(self, process_name: str) -> bool:
        """
        Установить флаг процесса, если он не установлен.

        :param process_name: Название процесса.
        :return: True, если флаг был установлен, False, если уже существует.
        """
        try:
            result = self.redis_client.setnx(process_name, 1)
            logger.debug("Process flag set for %s: %s", process_name, result)
            return result
        except Exception as e:
            logger.error(
                "Error setting process flag for %s: %s", process_name, e
            )
            return False

    def clear_process_flag(self, process_name: str) -> bool:
        """
        Очистить флаг процесса.

        :param process_name: Название процесса.
        :return: True, если флаг был успешно удалён, False в противном случае.
        """
        try:
            result = self.redis_client.delete(process_name)
            logger.debug(
                "Cleared process flag for %s: %s", process_name, result
            )
            return result > 0
        except Exception as e:
            logger.error(
                "Error clearing process flag for %s: %s", process_name, e
            )
            return False
