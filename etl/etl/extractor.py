import logging
import uuid
from contextlib import contextmanager
from typing import Dict, List

import backoff
import psycopg2
from config.settings import POSTGRES_CONFIG
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


@backoff.on_exception(
    backoff.expo,
    (psycopg2.OperationalError,),
    max_time=60,
    jitter=backoff.full_jitter,
)
def get_connection():
    """Создает и возвращает подключение к базе данных с автоматической повторной попыткой."""
    conn = psycopg2.connect(**POSTGRES_CONFIG)
    return conn


@contextmanager
def get_db_cursor():
    """Context manager для автоматического управления соединением и курсором с БД."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        logger.error(
            f"Database operation failed: {e}",
            exc_info=True,
        )
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


class Extractor:
    def convert_to_uuid(self, ids: List[str]) -> List[str]:
        """Преобразование списка строк в список UUID."""
        return [str(uuid.UUID(id_)) for id_ in ids]

    def fetch_new_filmworks(
        self, last_modified: str, batch_size: int = 100
    ) -> List[Dict]:
        """Извлекает новые фильмы, добавленные после последней метки времени."""
        query = """
        SELECT id, modified
        FROM content.film_work
        WHERE created > %s
        ORDER BY created
        LIMIT %s;
        """
        return self._fetch_data(query, (last_modified, batch_size))

    def fetch_modified_persons(
        self, last_modified: str, batch_size: int = 100
    ) -> List[Dict]:
        """Извлекает изменённых персон после последней метки времени."""
        query = """
        SELECT id, modified
        FROM content.person
        WHERE modified > %s
        ORDER BY modified
        LIMIT %s;
        """
        return self._fetch_data(query, (last_modified, batch_size))

    def fetch_persons_by_ids(self, person_ids: List[str]) -> List[Dict]:
        """Получает персон по списку ID, их роли и фильмы, и преобразует в нужный формат."""
        if not person_ids:
            return []
        placeholders = ", ".join(["%s"] * len(person_ids))
        query = f"""
        SELECT p.id, p.full_name, pfw.role, fw.id AS film_id, fw.title AS film_title
        FROM content.person p
        LEFT JOIN content.person_film_work pfw ON p.id = pfw.person_id
        LEFT JOIN content.film_work fw ON pfw.film_work_id = fw.id
        WHERE p.id IN ({placeholders});
        """
        persons = self._fetch_data(query, tuple(person_ids))
        person_map = {}
        for person in persons:
            person_id = person["id"]
            if person_id not in person_map:
                person_map[person_id] = {
                    "id": person["id"],
                    "full_name": person["full_name"],
                    "roles": [],
                    "films": [],
                }
            if person.get("role"):
                person_map[person_id]["roles"].append(person["role"])
            if person.get("film_id") and person.get("film_title"):
                film = {"id": person["film_id"], "title": person["film_title"]}
                person_map[person_id]["films"].append(film)
        return list(person_map.values())

    def fetch_modified_genres(
        self, last_modified: str, batch_size: int = 100
    ) -> List[Dict]:
        """Извлекает изменённые жанры после последней метки времени."""
        query = """
        SELECT id, modified, name, description
        FROM content.genre
        WHERE modified > %s
        ORDER BY modified
        LIMIT %s;
        """
        return self._fetch_data(query, (last_modified, batch_size))

    def fetch_related_filmworks_by_person(
        self, person_ids: List[str], batch_size: int = 100
    ) -> List[Dict]:
        """Извлекает фильмы, связанные с указанными персоналиями."""
        if not person_ids:
            return []
        query = """
        SELECT DISTINCT fw.id, fw.modified
        FROM content.film_work fw
        JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id
        WHERE pfw.person_id = ANY(%s::uuid[])
        ORDER BY fw.modified
        LIMIT %s;
        """
        return self._fetch_data(
            query, (self.convert_to_uuid(person_ids), batch_size)
        )

    def fetch_related_filmworks_by_genre(
        self, genre_ids: List[str], batch_size: int = 100
    ) -> List[Dict]:
        """Извлекает фильмы, связанные с указанными жанрами."""
        if not genre_ids:
            return []
        query = """
        SELECT DISTINCT fw.id, fw.modified
        FROM content.film_work fw
        JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id
        WHERE gfw.genre_id = ANY(%s::uuid[])
        ORDER BY fw.modified
        LIMIT %s;
        """
        return self._fetch_data(
            query, (self.convert_to_uuid(genre_ids), batch_size)
        )

    def fetch_full_filmwork_data(self, filmwork_ids: List[str]) -> List[Dict]:
        """Получает полные данные о фильмах, включая персоналии и жанры."""
        if not filmwork_ids:
            return []
        filmworks = self._fetch_filmwork_details(filmwork_ids)
        persons = self._fetch_person_data(filmwork_ids)
        genres = self._fetch_genre_data(filmwork_ids)
        return self._combine_data(filmworks, persons, genres)

    def _fetch_filmwork_details(self, filmwork_ids: List[str]) -> List[Dict]:
        query = """
        SELECT id AS fw_id, title, description, rating, type, created, modified
        FROM content.film_work
        WHERE id = ANY(%s::uuid[]);
        """
        return self._fetch_data(query, (self.convert_to_uuid(filmwork_ids),))

    def _fetch_person_data(self, filmwork_ids: List[str]) -> List[Dict]:
        query = """
        SELECT pfw.film_work_id, p.id AS person_id, p.full_name AS person_name, pfw.role
        FROM content.person_film_work pfw
        JOIN content.person p ON p.id = pfw.person_id
        WHERE pfw.film_work_id = ANY(%s::uuid[]);
        """
        return self._fetch_data(query, (self.convert_to_uuid(filmwork_ids),))

    def _fetch_genre_data(self, filmwork_ids: List[str]) -> List[Dict]:
        query = """
        SELECT gfw.film_work_id, g.id AS genre_id, g.name AS genre_name
        FROM content.genre_film_work gfw
        JOIN content.genre g ON g.id = gfw.genre_id
        WHERE gfw.film_work_id = ANY(%s::uuid[]);
        """
        return self._fetch_data(query, (self.convert_to_uuid(filmwork_ids),))

    def _combine_data(
        self, filmworks: List[Dict], persons: List[Dict], genres: List[Dict]
    ) -> List[Dict]:
        """Объединяет данные о фильмах, персоналиях и жанрах."""
        filmwork_dict = {fw["fw_id"]: fw for fw in filmworks}

        for person in persons:
            film_id = person["film_work_id"]
            if film_id in filmwork_dict:
                filmwork_dict[film_id].setdefault("persons", []).append(
                    {
                        "id": person["person_id"],
                        "name": person["person_name"],
                        "role": person["role"],
                    }
                )

        for genre in genres:
            film_id = genre["film_work_id"]
            if film_id in filmwork_dict:
                filmwork_dict[film_id].setdefault("genres", []).append(
                    {"id": genre["genre_id"], "name": genre["genre_name"]}
                )

        return list(filmwork_dict.values())

    def _fetch_data(self, query: str, params: tuple) -> List[Dict]:
        """Выполняет запрос к БД и возвращает результат."""
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
