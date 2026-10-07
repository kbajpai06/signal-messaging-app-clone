from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

SQLITE_PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA busy_timeout=5000",
    "PRAGMA foreign_keys=ON",
    "PRAGMA temp_store=MEMORY",
)


def _ensure_sqlite_parent_dir(database_url: str) -> None:
    url = make_url(database_url)
    if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
        Path(url.database).parent.mkdir(parents=True, exist_ok=True)


def build_engine(database_url: str, *, echo: bool = False) -> AsyncEngine:
    _ensure_sqlite_parent_dir(database_url)
    engine = create_async_engine(database_url, echo=echo)

    if engine.dialect.name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def _apply_pragmas(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            for pragma in SQLITE_PRAGMAS:
                cursor.execute(pragma)
            cursor.close()

    return engine


def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_models(engine: AsyncEngine) -> None:
    """Create tables if missing (no Alembic: documented assumption)."""
    import app.models  # noqa: F401  (registers all tables on Base.metadata)
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
