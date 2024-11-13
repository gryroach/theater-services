import logging
from typing import Any


class Transformer:
    @staticmethod
    def transform(
        raw_data: list[dict[str, Any]], data_type: str
    ) -> list[dict[str, str | list[dict[str, str]]]]:
        """Преобразует необработанные данные в нужный формат на основе типа данных."""
        if data_type == "movies":
            return Transformer.transform_movies(raw_data)
        elif data_type == "genres":
            return [Transformer.transform_genre(record) for record in raw_data]
        elif data_type == "persons":
            return [
                Transformer.transform_person(record) for record in raw_data
            ]
        else:
            logging.warning(
                f"Неизвестный тип данных для трансформации: {data_type}"
            )
            return []

    @staticmethod
    def transform_movies(
        raw_data: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Преобразует данные фильмов."""
        transformed_data = []
        for record in raw_data:
            transformed_record = {
                "id": record.get("fw_id"),
                "imdb_rating": record.get("rating"),
                "genres": [
                    genre["name"]
                    for genre in record["genres"]
                    if record.get("genres")
                ],
                "genres_details": Transformer.extract_genres(record),
                "title": record.get("title"),
                "description": record.get("description"),
                "directors": Transformer.extract_people_by_role(
                    record, "director"
                ),
                "actors": Transformer.extract_people_by_role(record, "actor"),
                "writers": Transformer.extract_people_by_role(
                    record, "writer"
                ),
            }
            transformed_record["directors_names"] = [
                d["name"] for d in transformed_record["directors"]
            ]
            transformed_record["actors_names"] = [
                a["name"] for a in transformed_record["actors"]
            ]
            transformed_record["writers_names"] = [
                w["name"] for w in transformed_record["writers"]
            ]
            transformed_data.append(transformed_record)
        return transformed_data

    @staticmethod
    def transform_genre(record: dict[str, Any]) -> dict[str, Any]:
        """Преобразует запись для индекса жанров."""
        return {
            "id": record.get("id"),
            "name": record.get("name"),
            "description": record.get("description"),
        }

    @staticmethod
    def transform_person(record: dict[str, Any]) -> dict[str, Any]:
        """Преобразует запись для индекса персон."""
        return {
            "id": record.get("id"),
            "full_name": record.get("full_name"),
            "films": record.get("films", []),
        }

    @staticmethod
    def extract_genres(record: dict[str, Any]) -> list[dict[str, str]]:
        """Извлекает жанры из записи."""
        return [
            {"id": genre["id"], "name": genre["name"]}
            for genre in record.get("genres", [])
        ]

    @staticmethod
    def extract_people_by_role(
        record: dict[str, Any], role: str
    ) -> list[dict[str, str]]:
        """Извлекает людей определенной роли из записи."""
        return [
            {"id": person["id"], "name": person["name"]}
            for person in record.get("persons", [])
            if person.get("role") == role
        ]
