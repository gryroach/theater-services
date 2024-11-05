from datetime import datetime
from typing import Generator, Any

from psycopg import connection as _connection

from sql_templates import query

BATCH_SIZE = 100


class PostgresExtractor:
    def __init__(self, connection: _connection) -> None:
        self.connection = connection

    def get_data(self, last_sync_date: datetime | str) -> Generator[list[Any], None, None]:
        with self.connection.cursor() as cursor:
            cursor.execute(query, [last_sync_date])
            while results := cursor.fetchmany(size=BATCH_SIZE):
                yield results
