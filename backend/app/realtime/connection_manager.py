import asyncio
from collections.abc import Collection, Mapping
from typing import Any

from app.realtime.connection import Connection
from app.realtime.protocol import CLOSE_UNAUTHENTICATED, encode_frame, server_frame


class ConnectionManager:
    """In-memory user_id -> sockets registry. Implements RealtimeGateway.

    Correct for a single-process deployment (which SQLite requires anyway). Scaling out
    means swapping this class for a Redis pub/sub gateway; no service would change.
    """

    def __init__(self) -> None:
        self._by_user: dict[str, set[Connection]] = {}

    def register(self, connection: Connection) -> bool:
        """Returns True if this is the user's first live socket (they just came online)."""
        sockets = self._by_user.setdefault(connection.user_id, set())
        first = not sockets
        sockets.add(connection)
        return first

    def unregister(self, connection: Connection) -> bool:
        """Returns True if that was the user's last socket (they just went offline)."""
        sockets = self._by_user.get(connection.user_id)
        if not sockets or connection not in sockets:
            return False
        sockets.discard(connection)
        if sockets:
            return False
        del self._by_user[connection.user_id]
        return True

    def is_online(self, user_id: str) -> bool:
        return bool(self._by_user.get(user_id))

    async def publish_to_users(
        self, user_ids: Collection[str], event_type: str, payload: Mapping[str, Any]
    ) -> None:
        targets = [c for uid in set(user_ids) for c in self._by_user.get(uid, ())]
        if not targets:
            return
        data = encode_frame(server_frame(event_type, dict(payload)))  # serialize once
        await asyncio.gather(*(c.send_text(data) for c in targets))

    async def close_session(self, session_id: str) -> None:
        targets = [c for s in self._by_user.values() for c in s if c.session_id == session_id]
        await asyncio.gather(*(c.close(CLOSE_UNAUTHENTICATED, "session revoked") for c in targets))

    async def close_all(self, code: int) -> None:
        targets = [c for sockets in self._by_user.values() for c in sockets]
        await asyncio.gather(*(c.close(code, "server shutting down") for c in targets))
