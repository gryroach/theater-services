from elasticsearch import Elasticsearch, helpers

from backoff import backoff
from logger import logger
from schemas import es_schema


class ElasticsearchLoader:
    def __init__(self, host: str) -> None:
        self.host = host
        self.index_name = 'movies'
        self.create_index()

    def create_index(self) -> None:
        with Elasticsearch(self.host) as client:
            if not client.indices.exists(index=self.index_name):
                client.indices.create(index=self.index_name, body=es_schema)
            logger.info(f'Индекс %s успешно создан.', self.index_name)

    @backoff()
    def load_data(self, data: list[dict]) -> None:
        with Elasticsearch(self.host) as client:
            actions = (
                {'_index': self.index_name, '_id': doc['id'], '_source': doc}
                for doc in data
            )
            helpers.bulk(client=client, actions=actions)
