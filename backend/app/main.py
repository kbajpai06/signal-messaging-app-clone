from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import build_engine, build_session_factory, init_models
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.realtime.connection_manager import ConnectionManager
from app.realtime.context import RealtimeRuntime
from app.realtime.protocol import CLOSE_GOING_AWAY
from app.realtime.rate_limit import TYPING_MIN_INTERVAL_MS, MinIntervalLimiter
from app.realtime.ws_endpoint import router as ws_router
from app.seed.seed_data import seed_if_empty
from app.services.events import EventPublisher
from app.services.storage import LocalFileStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    # The ConnectionManager IS the RealtimeGateway: services only ever see EventPublisher.
    manager = ConnectionManager()
    events = EventPublisher(manager)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings.database_url)
        session_factory = build_session_factory(engine)
        await init_models(engine)
        if settings.seed_on_startup:
            await seed_if_empty(session_factory)
        app.state.engine = engine
        app.state.session_factory = session_factory
        app.state.realtime = RealtimeRuntime(
            session_factory=session_factory,
            settings=settings,
            manager=manager,
            events=events,
            typing_limiter=MinIntervalLimiter(TYPING_MIN_INTERVAL_MS),
        )
        try:
            yield
        finally:
            await manager.close_all(CLOSE_GOING_AWAY)
            await engine.dispose()

    app = FastAPI(title="Signal Clone API", version="0.4.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.gateway = manager
    app.state.events = events

    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)
    app.state.file_storage = LocalFileStorage(upload_root)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router)  # wss://<host>/ws
    # Avatars are non-sensitive, so a static mount is enough (filenames are random UUIDs).
    app.mount("/uploads", StaticFiles(directory=upload_root), name="uploads")
    return app


app = create_app()
