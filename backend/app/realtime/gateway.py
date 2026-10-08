from collections.abc import Collection, Mapping
from typing import Any, Protocol


class RealtimeGateway(Protocol):
    """What services need from the realtime layer. Services never import WebSocket types."""

    def is_online(self, user_id: str) -> bool: ...

    async def publish_to_users(
        self, user_ids: Collection[str], event_type: str, payload: Mapping[str, Any]
    ) -> None: ...

    async def close_session(self, session_id: str) -> None:
        """Drop every live socket that belongs to a (just revoked) login session."""
        ...


class NullGateway:
    """No-op gateway, kept for scripts and tools that run without a WebSocket server."""

    def is_online(self, user_id: str) -> bool:
        return False

    async def publish_to_users(
        self, user_ids: Collection[str], event_type: str, payload: Mapping[str, Any]
    ) -> None:
        return None

    async def close_session(self, session_id: str) -> None:
        return None
