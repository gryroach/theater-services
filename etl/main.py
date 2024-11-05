from contextlib import closing
from time import sleep

import psycopg
from psycopg import ClientCursor
from psycopg.rows import class_row

from logger import logger
from extract import PostgresExtractor
from load import ElasticsearchLoader
from schemas import Movie
from storage import State, RedisStorage
from settings import es_settings, pg_settings

dsl = pg_settings.get_dsl()
es_host = es_settings.get_url()


def update_index() -> None:
    with closing(psycopg.connect(**dsl, row_factory=class_row(Movie), cursor_factory=ClientCursor)) as pg_conn:
        state = State(RedisStorage())
        extractor = PostgresExtractor(pg_conn)
        loader = ElasticsearchLoader(es_host)

        for row in extractor.get_data(state.get_state('last_sync_date')):
            data, dates = [], []
            for item in row:
                movie = item.model_dump()
                dates.append(movie.pop('last_modified_date'))
                data.append(movie)

            loader.load_data(data)
            last_modified_date = max(dates)
            state.set_state('last_sync_date', last_modified_date.isoformat())


if __name__ == '__main__':
    while True:
        try:
            update_index()
        except Exception as e:
            logger.error(e)
        finally:
            sleep(60)
