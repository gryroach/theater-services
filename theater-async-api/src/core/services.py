from elasticsearch import AsyncElasticsearch


class BaseService:
    def __init__(self, elastic: AsyncElasticsearch):
        self.elastic = elastic
