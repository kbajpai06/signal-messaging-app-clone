from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.models import User
from app.realtime.connection import Connection
from app.realtime.connection_manager import ConnectionManager
from app.realtime.protocol import error_frame, server_frame
from app.realtime.rate_limit import MinIntervalLimiter
from app.schemas.ws_events import ClientEnvelope
from app.services.events import EventPublisher


@dataclass(frozen=True)
class RealtimeRuntime:
    """Process-wide realtime dependencies (built once in the app lifespan)."""

    session_factory: async_sessionmaker[AsyncSession]
    settings: Settings
    manager: ConnectionManager
    events: EventPublisher
    typing_limiter: MinIntervalLimiter


@dataclass(frozen=True)
class ConnectionContext:
    """Everything a handler needs about the socket that sent the event."""

    user: User
    connection: Connection
    expires_at: int
    runtime: RealtimeRuntime

    @property
    def user_id(self) -> str:
        return self.user.id

    @asynccontextmanager
    async def db(self) -> AsyncIterator[AsyncSession]:
        """Short-lived session per event; services commit explicitly."""
        async with self.runtime.session_factory() as session:
            yield session

    async def reply(
        self, request: ClientEnvelope, event_type: str, payload: dict[str, Any]
    ) -> None:
        await self.connection.send(server_frame(event_type, payload, reply_to=request.id))

    async def reply_error(self, request: ClientEnvelope, code: str, message: str) -> None:
        await self.connection.send(error_frame(request.id, code, message))
