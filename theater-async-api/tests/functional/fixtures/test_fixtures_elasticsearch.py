import pytest_asyncio
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from tests.functional.settings import (
    es_genres_settings,
    es_movies_settings,
    es_persons_settings,
    test_settings,
)

INDEX_SETTINGS_MAP = {
    "movies": es_movies_settings,
    "genres": es_genres_settings,
    "persons": es_persons_settings,
}


@pytest_asyncio.fixture(name="es_client", scope="session")
async def es_client() -> AsyncElasticsearch:
    """
    Создает клиент Elasticsearch для работы с асинхронным API.
    """
    client = AsyncElasticsearch(
        hosts=test_settings.elasticsearch_url, verify_certs=False
    )
    yield client
    await client.close()


@pytest_asyncio.fixture(name="clear_es_indices")
def clear_es_indices(es_client: AsyncElasticsearch):
    """
    Удаляет указанный индекс в Elasticsearch.
    """

    async def inner(
        index_name: str,
    ) -> None:
        es_settings = INDEX_SETTINGS_MAP[index_name]
        if await es_client.indices.exists(index=es_settings.es_index):
            await es_client.indices.delete(index=es_settings.es_index)

    return inner


@pytest_asyncio.fixture(name="es_write_data")
def es_write_data(es_client: AsyncElasticsearch):
    """
    Записывает данные в указанный индекс Elasticsearch.
    """

    async def inner(data: list[dict], index_name: str, prepare: bool = True) -> None:
        es_settings = INDEX_SETTINGS_MAP[index_name]
        if await es_client.indices.exists(index=es_settings.es_index):
            await es_client.indices.delete(index=es_settings.es_index)
        await es_client.indices.create(
            index=es_settings.es_index, **es_settings.es_index_mapping
        )
        if prepare:
            data = prepare_data_for_es(data, es_settings.es_index)
        updated, errors = await async_bulk(
            client=es_client,
            actions=data,
            refresh=True,
        )
        if errors:
            raise Exception("Ошибка записи данных в Elasticsearch")

    return inner


def prepare_data_for_es(in_data: list[dict], index_name: str) -> list[dict]:
    """
    Преобразует данные для загрузки в Elasticsearch.

    Args:
        in_data (list[dict]): Исходные данные.
        index_name (str): Имя индекса.

    Returns:
        list[dict]: Преобразованные данные.
    """
    return [{"_index": index_name, "_id": row["id"], "_source": row} for row in in_data]
