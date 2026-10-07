from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.health import router as health_router
from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import build_engine, build_session_factory, init_models
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.seed.seed_data import seed_if_empty


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings.database_url)
        session_factory = build_session_factory(engine)
        await init_models(engine)
        if settings.seed_on_startup:
            await seed_if_empty(session_factory)
        app.state.engine = engine
        app.state.session_factory = session_factory
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title="Signal Clone API", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings

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
    return app


app = create_app()
