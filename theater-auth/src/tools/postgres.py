import typer

from db.db import Base, engine
from utils import coro

app = typer.Typer()


@app.command()
@coro
async def create_database() -> None:
    # Импортирование всех моделей
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.command()
@coro
async def purge_database() -> None:
    # Импортирование всех моделей
    import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


if __name__ == "__main__":
    app()
