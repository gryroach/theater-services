from backoff import backoff
from elasticsearch import Elasticsearch, helpers
from logger import logger
from schemas import genres_schema, movies_schema, persons_schema


class ElasticsearchLoader:
    def __init__(self, host: str) -> None:
        self.host = host
        self.index_schemas = {
            "movies": movies_schema,
            "genres": genres_schema,
            "persons": persons_schema,
        }
        self.create_indices()

    def create_indices(self) -> None:
        with Elasticsearch(self.host) as client:
            for index_name, schema in self.index_schemas.items():
                if not client.indices.exists(index=index_name):
                    client.indices.create(index=index_name, body=schema)
                    logger.info(f"Индекс %s успешно создан.", index_name)

    @backoff()
    def load_to_index(self, data: list[dict], index_name: str) -> None:
        with Elasticsearch(self.host) as client:
            actions = (
                {"_index": index_name, "_id": doc["id"], "_source": doc}
                for doc in data
            )
            helpers.bulk(client=client, actions=actions)
            logger.info(
                f"Успешно загружено {len(data)} документов в индекс {index_name}."
            )
