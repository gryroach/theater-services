import abc
import datetime
import json
from typing import Any, Dict, Optional

from redis import Redis

from logger import logger


class BaseStorage(abc.ABC):
    """Абстрактное хранилище состояния.

    Позволяет сохранять и получать состояние.
    Способ хранения состояния может варьироваться в зависимости
    от итоговой реализации. Например, можно хранить информацию
    в базе данных или в распределённом файловом хранилище.
    """

    @abc.abstractmethod
    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""

    @abc.abstractmethod
    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""


class JsonFileStorage(BaseStorage):
    """Реализация хранилища, использующего локальный файл.

    Формат хранения: JSON
    """

    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path

    def save_state(self, state: Dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        with open(self.file_path, 'w') as file:
            json.dump(state, file)

    def retrieve_state(self) -> Dict[str, Any]:
        """Получить состояние из хранилища."""
        try:
            with open(self.file_path) as file:
                try:
                    state = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    state = {}
                    logger.error('Произошла ошибка: %s', e, exc_info=True)
                return state
        except FileNotFoundError:
            logger.error('Файл %s не найден.', self.file_path)
            return {}


class RedisStorage(BaseStorage):
    """Реализация хранилища, использующего Redis."""

    def __init__(self) -> None:
        self.connection: Redis = Redis.from_url(
            "redis://redis:6379/0",
            decode_responses=True
        )

    def save_state(self, state: dict[str, Any]) -> None:
        """Сохранить состояние в хранилище."""
        self.connection.mset(state)

    def retrieve_state(self) -> dict[str, Any]:
        """Получить состояние из хранилища."""
        state = {}
        for key in self.connection.scan_iter():
            state[key] = self.connection.get(key)
        return state


class State:
    """Класс для работы с состояниями."""

    def __init__(self, storage: BaseStorage) -> None:
        self.storage = storage

    def set_state(self, key: str, value: Any) -> None:
        """Установить состояние для определённого ключа."""
        state = self.storage.retrieve_state()
        state[key] = value
        self.storage.save_state(state)

    def get_state(self, key: str) -> Any:
        """Получить состояние по определённому ключу."""
        state = self.storage.retrieve_state()
        return state.get(key) or datetime.datetime.min
