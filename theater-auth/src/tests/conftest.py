import asyncio
from typing import AsyncGenerator

import asyncpg
import pytest
import pytest_asyncio
from _pytest.monkeypatch import MonkeyPatch
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    AsyncTransaction,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings
from main import app
from models import Base


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """
    Создает и возвращает event loop для сессии тестов.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


async def create_database() -> None:
    db_configs = {
        "user": settings.postgres_user,
        "password": settings.postgres_password,
        "host": settings.postgres_host,
        "port": settings.postgres_port,
    }
    conn = await asyncpg.connect(**db_configs)
    await conn.execute(f"DROP DATABASE IF EXISTS {settings.test_db}")
    await conn.execute(f"CREATE DATABASE {settings.test_db}")
    await conn.close()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    engine_ = create_async_engine(
        settings.test_database_dsn, future=True, poolclass=NullPool
    )
    try:
        yield engine_
    finally:
        await engine_.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_db(engine: AsyncEngine) -> None:
    await create_database()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_connection(
    engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    async with engine.connect() as connection:
        yield connection


@pytest_asyncio.fixture(autouse=True)
async def db_transaction(
    db_connection: AsyncConnection,
) -> AsyncGenerator[AsyncTransaction, None]:
    async with db_connection.begin() as transaction:
        yield transaction
        await transaction.rollback()


@pytest_asyncio.fixture()
async def session(
    db_connection: AsyncConnection, monkeypatch: MonkeyPatch
) -> AsyncGenerator[AsyncSession, None]:
    session_maker = async_sessionmaker(db_connection, expire_on_commit=False)
    monkeypatch.setattr("db.db.async_session", session_maker)
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture()
async def client(
    monkeypatch: MonkeyPatch,
) -> AsyncGenerator[AsyncClient, None]:
    monkeypatch.setattr(
        "core.config.settings.redis_host",
        settings.test_redis_host,
    )
    monkeypatch.setattr(
        "core.config.settings.redis_port",
        settings.test_redis_port,
    )
    monkeypatch.setattr(
        "core.config.settings.redis_db",
        settings.test_redis_db,
    )
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app),
            base_url="http://test",
        ) as client:
            yield client
