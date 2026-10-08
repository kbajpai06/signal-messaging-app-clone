from collections.abc import Collection

from app.core.uow import UnitOfWork
from app.models import User
from app.repositories.presence_repo import PresenceRepository
from app.services.events import EventPublisher
from app.utils.time import now_ms


class PresenceService:
    def __init__(
        self, *, presence: PresenceRepository, events: EventPublisher, uow: UnitOfWork
    ) -> None:
        self._presence = presence
        self._events = events
        self._uow = uow

    async def peer_ids(self, user_id: str) -> list[str]:
        return await self._presence.peer_user_ids(user_id)

    async def announce_online(self, user: User, audience: Collection[str]) -> None:
        await self._events.presence_update(
            audience, user_id=user.id, online=True, last_seen_at=user.last_seen_at
        )

    async def announce_offline(self, user_id: str) -> None:
        """Last socket closed: stamp last_seen_at, then tell the people who can see it."""
        seen_at = now_ms()
        await self._presence.set_last_seen(user_id, seen_at)
        await self._uow.commit()
        audience = await self._presence.peer_user_ids(user_id)
        await self._events.presence_update(
            audience, user_id=user_id, online=False, last_seen_at=seen_at
        )
