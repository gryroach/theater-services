import os
import time
from contextlib import closing
from datetime import datetime

import psycopg
from elasticsearch import Elasticsearch, NotFoundError
from extract import PostgresExtractor
from load import ElasticsearchLoader
from logger import logger
from psycopg.rows import dict_row
from settings import es_settings, pg_settings
from storage import RedisStorage, State

dsl = pg_settings.get_dsl()
es_host = es_settings.get_url()
es_client = Elasticsearch(es_host)


def segregate_data(rows):
    movies, genres, persons, dates = [], [], [], []
    seen_persons = set()
    seen_genres = set()
    for item in rows:
        try:
            logger.debug(f"Обрабатываем элемент: {item}")
            if "id" in item and "title" in item:
                movies.append(item)
            if "genres" in item and isinstance(item["genres"], list):
                for genre in item["genres"]:
                    if isinstance(genre, dict) and "id" in genre:
                        genre_id = genre["id"]
                        if genre_id not in seen_genres:
                            genres.append(genre)
                            seen_genres.add(genre_id)
            for role in ["directors", "actors", "writers"]:
                if role in item:
                    for person in item[role]:
                        if isinstance(person, dict) and "id" in person:
                            person_id = person["id"]
                            if person_id not in seen_persons:
                                persons.append(person)
                                seen_persons.add(person_id)
            if "last_modified_date" in item:
                dates.append(item["last_modified_date"])
        except Exception as e:
            logger.error(f"Ошибка при обработке элемента {item}: {e}")
    logger.info(
        f"Сегрегированные данные: {len(movies)} фильмов, {len(genres)} жанров, {len(persons)} персон."
    )
    return movies, genres, persons, dates


def get_last_modified_date(dates):
    return max(dates) if dates else None


def load_data(loader, data, index_name):
    if data:
        logger.info(f"Загружаем {len(data)} записей в индекс {index_name}.")
        loader.load_to_index(data, index_name)
    else:
        logger.info(f"Нет новых данных для загрузки в индекс {index_name}.")


def reset_elasticsearch_indexes():
    logger.info("Выполняем сброс индексов и начальную настройку...")
    index_names = ["movies", "genres", "persons"]
    for index in index_names:
        try:
            if es_client.indices.exists(index=index):
                es_client.indices.delete(index=index)
                logger.info(f"Индекс '{index}' удалён.")
        except NotFoundError:
            logger.warning(f"Индекс '{index}' не найден. Пропускаем удаление.")
    for index in index_names:
        es_client.indices.create(index=index, ignore=400)
        logger.info(f"Индекс '{index}' пересоздан.")


def update_index():
    with closing(psycopg.connect(**dsl, row_factory=dict_row)) as pg_conn:
        state = State(RedisStorage())
        extractor = PostgresExtractor(pg_conn)
        loader = ElasticsearchLoader(es_host)

        last_sync_date = state.get_state("last_sync_date")
        if last_sync_date is None:
            last_sync_date = datetime(1970, 1, 1)

        rows_updated = 0

        for batch_idx, rows in enumerate(extractor.get_data(last_sync_date)):
            logger.info(
                f"Обрабатываем пакет {batch_idx + 1} (размер: {len(rows)} записей)"
            )
            movies, genres, persons, dates = segregate_data(rows)
            logger.info(
                f"Найдено {len(movies)} фильмов, {len(genres)} жанров, {len(persons)} персон для обработки."
            )
            load_data(loader, movies, "movies")
            load_data(loader, genres, "genres")
            load_data(loader, persons, "persons")

            rows_updated += len(movies) + len(genres) + len(persons)

            last_modified_date = get_last_modified_date(dates)
            if last_modified_date:
                state.set_state(
                    "last_sync_date", last_modified_date.isoformat()
                )

        if rows_updated > 0:
            logger.info(f"Обновлено {rows_updated} записей в Elasticsearch.")
        else:
            logger.info("Обновлений не обнаружено.")


if __name__ == "__main__":
    is_clean_start = os.getenv("ETL_CLEAN_START", "false").lower() == "true"
    state = State(RedisStorage())
    logger.info(f"Чистый запуск: {is_clean_start}")

    if is_clean_start:
        logger.info(
            "Чистый запуск обнаружен. Сбросим индексы и установим начальную дату."
        )
        reset_elasticsearch_indexes()
        state.set_state("ETL_CLEAN_START", False)
        state.set_state("last_sync_date", datetime(1970, 1, 1).isoformat())

    while True:
        try:
            update_index()
        except Exception as e:
            logger.error(f"Ошибка при обновлении индекса: {e}", exc_info=True)
        finally:
            time.sleep(10)
