from collections.abc import Collection, Mapping
from typing import Any, Protocol


class RealtimeGateway(Protocol):
    """What services need from the realtime layer. Services never import WebSocket types."""

    def is_online(self, user_id: str) -> bool: ...

    async def publish_to_users(
        self, user_ids: Collection[str], event_type: str, payload: Mapping[str, Any]
    ) -> None: ...


class NullGateway:
    """Default until the WebSocket ConnectionManager lands in Phase 4."""

    def is_online(self, user_id: str) -> bool:
        return False

    async def publish_to_users(
        self, user_ids: Collection[str], event_type: str, payload: Mapping[str, Any]
    ) -> None:
        return None
