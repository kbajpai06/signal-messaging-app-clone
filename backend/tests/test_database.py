from pathlib import Path

from sqlalchemy import text

from app.core.database import build_engine, build_session_factory, init_models


async def test_sqlite_pragmas_are_applied(tmp_path: Path) -> None:
    engine = build_engine(f"sqlite+aiosqlite:///{tmp_path / 'pragma.db'}")
    await init_models(engine)
    async with build_session_factory(engine)() as session:
        assert await session.scalar(text("PRAGMA foreign_keys")) == 1
        assert str(await session.scalar(text("PRAGMA journal_mode"))).lower() == "wal"
        assert await session.scalar(text("PRAGMA busy_timeout")) == 5000
    await engine.dispose()
