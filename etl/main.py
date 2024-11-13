import logging
import os
import random
import time
from datetime import datetime
from multiprocessing import Process
from typing import Any

import backoff
from config.settings import (
    ES_CONFIG,
    FIRST_TIME_STARTED,
    MAX_BACKOFF,
    MAX_RETRIES,
    REDIS_CONFIG,
    genres_schema,
    movies_schema,
    persons_schema,
)
from dotenv import load_dotenv
from elastic_transport import ConnectionError
from elasticsearch import Elasticsearch, NotFoundError
from elasticsearch.exceptions import ConflictError
from psycopg2 import OperationalError
from redis.exceptions import RedisError
from storage.redis_state import RedisStateManager
from urllib3.connection import NewConnectionError

from etl.extractor import Extractor
from etl.loader import Loader
from etl.transformer import Transformer

load_dotenv()


def get_log_level(level_name):
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)


logging.basicConfig(
    level=get_log_level(os.getenv("CONSOLE_LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class ETLProcess:
    def __init__(
        self,
        redis_config: dict[str, Any],
        first_time: bool = False,
    ) -> None:
        self.redis_manager = RedisStateManager(redis_config)
        self.loader = Loader(Elasticsearch(**ES_CONFIG))
        self.extractor = Extractor()
        self.schemas = {
            "movies": movies_schema,
            "genres": genres_schema,
            "persons": persons_schema,
        }
        self.tables = {
            "film_work": "film_work_index",
            "genre": "genre_index",
            "person": "person_index",
        }
        self.initialize = first_time
        self.process_name = "etl_process_flag"

    @backoff.on_exception(
        backoff.expo,
        (
            ConnectionError,
            OperationalError,
            RedisError,
            NotFoundError,
            ConflictError,
            ConnectionRefusedError,
            NewConnectionError,
        ),
        max_time=MAX_BACKOFF,
        max_tries=MAX_RETRIES,
        jitter=backoff.random_jitter,
    )
    def initialize_index(self, index_type: str) -> None:
        try:
            if not self.redis_manager.set_process_flag(self.process_name):
                logging.info("Процесс уже запущен другим экземпляром.")
                return
            schema = self.schemas.get(index_type)
            if not schema:
                logging.error(
                    f"Неизвестный тип индекса: {index_type}",
                    exc_info=True,
                )
                return
            if self.loader.index_exists(index_type):
                self.loader.delete_index(index_type)
                logging.info(
                    f"Index '{index_type}' deleted from Elasticsearch."
                )
            self.loader.create_index(index_type, schema)
            logging.info(f"Index '{index_type}' created in Elasticsearch.")
        except Exception as e:
            logging.error(f"Ошибка инициализации индекса: {e}", exc_info=True)
        finally:
            self.redis_manager.clear_process_flag(self.process_name)

    def run_etl_process(self) -> None:
        if not self.redis_manager.set_process_flag(self.process_name):
            logging.info("Процесс уже запущен другим экземпляром.")
            return
        try:
            last_modified_times = self.get_last_modified_times()
            modified_persons = self.extractor.fetch_modified_persons(
                last_modified_times["person"]
            )
            modified_genres = self.extractor.fetch_modified_genres(
                last_modified_times["genre"]
            )
            new_filmworks = self.extractor.fetch_new_filmworks(
                last_modified_times["film_work"]
            )
            if not (modified_persons or modified_genres or new_filmworks):
                logging.debug("Нет изменений для обработки.")
                return
            filmwork_ids = self.get_filmwork_ids(
                modified_persons, modified_genres, new_filmworks
            )
            self.process_filmworks(filmwork_ids, last_modified_times)
            if modified_genres:
                transformed_genres = Transformer.transform(
                    modified_genres, "genres"
                )
                self.loader.load_data("genres", transformed_genres)
                last_modified_times["genre"] = self.get_max_modified_time(
                    modified_genres
                )
            if modified_persons:
                modified_persons_ids = [
                    person["id"] for person in modified_persons
                ]
                modified_persons_updates = self.extractor.fetch_persons_by_ids(
                    modified_persons_ids
                )
                transformed_persons = Transformer.transform(
                    modified_persons_updates, "persons"
                )
                self.loader.load_data("persons", transformed_persons)
                last_modified_times["person"] = self.get_max_modified_time(
                    modified_persons
                )
            self.update_last_modified(last_modified_times)

        except (
            RedisError,
            ConnectionError,
            NotFoundError,
            OperationalError,
            ConnectionRefusedError,
            NewConnectionError,
        ) as e:
            logging.error(
                f"Ошибка базы данных или доступа: {e}. Ожидание следующей попытки.",
                exc_info=True,
            )
            raise
        except Exception as e:
            logging.error(
                f"Unexpected error during ETL process: {e}", exc_info=True
            )
        finally:
            self.redis_manager.clear_process_flag(self.process_name)

    def get_last_modified_times(self) -> dict[str, datetime | None]:
        return {
            "person": self.redis_manager.get_last_modified("person"),
            "genre": self.redis_manager.get_last_modified("genre"),
            "film_work": self.redis_manager.get_last_modified("film_work"),
        }

    def get_max_modified_time(
        self, items: list[dict[str, Any]]
    ) -> datetime | None:
        return max((item["modified"] for item in items), default=None)

    def get_filmwork_ids(
        self,
        modified_persons: list[dict[str, Any]],
        modified_genres: list[dict[str, Any]],
        new_filmworks: list[dict[str, Any]],
    ) -> list[str]:
        try:
            filmwork_ids_by_person = [
                fw["id"]
                for fw in self.extractor.fetch_related_filmworks_by_person(
                    [person["id"] for person in modified_persons]
                )
            ]
            filmwork_ids_by_genre = [
                fw["id"]
                for fw in self.extractor.fetch_related_filmworks_by_genre(
                    [genre["id"] for genre in modified_genres]
                )
            ]
            new_filmworks_ids = [
                new_filmwork["id"] for new_filmwork in new_filmworks
            ]
            return list(
                set(
                    filmwork_ids_by_person
                    + filmwork_ids_by_genre
                    + new_filmworks_ids
                )
            )
        except (
            RedisError,
            ConnectionError,
            NotFoundError,
            OperationalError,
        ) as e:
            logging.error(
                f"Ошибка при получении ID фильмов: {e}",
                exc_info=True,
            )
            raise

    def process_filmworks(
        self,
        filmwork_ids: list[str],
        last_modified_times: dict[str, datetime | None],
    ) -> None:
        try:
            full_filmwork_data = self.extractor.fetch_full_filmwork_data(
                filmwork_ids
            )
            if not full_filmwork_data:
                logging.warning("Нет данных для обработки.")
                return
            transformed_data = Transformer.transform(
                full_filmwork_data, "movies"
            )
            self.loader.load_data("movies", transformed_data)
            logging.info("Индексы обновлены!")
            last_modified_times["film_work"] = self.get_max_modified_time(
                full_filmwork_data
            )
        except (
            RedisError,
            ConnectionError,
            NotFoundError,
            OperationalError,
        ) as e:
            logging.error(
                f"Ошибка при обработке фильмов: {e}",
                exc_info=True,
            )
            raise

    def update_last_modified(
        self, last_modified_times: dict[str, datetime | None]
    ) -> None:
        for table, modified_time in last_modified_times.items():
            if modified_time is not None:
                modified_time = self.convert_to_datetime(modified_time)
                self.redis_manager.set_last_modified(table, modified_time)
        logging.debug(
            "Обновлены временные метки для всех таблиц: {}".format(
                [
                    self.redis_manager.get_last_modified(key)
                    for key in self.tables.keys()
                ]
            )
        )

    def convert_to_datetime(self, modified_time: Any) -> datetime | None:
        if isinstance(modified_time, str):
            return datetime.fromisoformat(modified_time.replace("Z", "+00:00"))
        return modified_time

    def start(self) -> None:
        last_modified_times = self.get_last_modified_times()
        if (
            any(value is not True for value in last_modified_times.values())
            or self.initialize
        ):
            for schema in self.schemas.keys():
                self.initialize_index(schema)
            self.reset_last_modified()
        while True:
            self.run_etl_process()
            interval = random.uniform(0.5, 0.9)
            time.sleep(interval)
            logging.debug(f"Refresh {interval} seconds")

    def reset_last_modified(self) -> None:
        initial_timestamp = datetime(1970, 1, 1, 0, 0)
        self.redis_manager.set_last_modified("film_work", initial_timestamp)
        self.redis_manager.set_last_modified("genre", initial_timestamp)
        self.redis_manager.set_last_modified("person", initial_timestamp)


def start_etl_process(redis_config: dict[str, Any], first_time: bool) -> None:
    etl_process = ETLProcess(redis_config, first_time=first_time)
    etl_process.start()


if __name__ == "__main__":
    processes: list[Process] = []
    for _ in range(1):
        process = Process(
            target=start_etl_process,
            args=(REDIS_CONFIG, FIRST_TIME_STARTED),
        )
        processes.append(process)
        process.start()
    for process in processes:
        process.join()
