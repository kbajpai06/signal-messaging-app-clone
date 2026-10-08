import logging
from collections.abc import Collection

from app.realtime.gateway import RealtimeGateway
from app.schemas.conversation import ConversationDetailOut
from app.schemas.message import MessageOut

logger = logging.getLogger(__name__)


class EventPublisher:
    """The only place that knows event names and payload shapes. Always called post-commit."""

    def __init__(self, gateway: RealtimeGateway) -> None:
        self._gateway = gateway

    def is_online(self, user_id: str) -> bool:
        return self._gateway.is_online(user_id)

    async def message_new(self, user_ids: Collection[str], message: MessageOut) -> None:
        await self._publish(user_ids, "message.new", {"message": message.model_dump(mode="json")})

    async def conversation_updated(
        self, user_ids: Collection[str], conversation: ConversationDetailOut
    ) -> None:
        await self._publish(
            user_ids, "conversation.updated", {"conversation": conversation.model_dump(mode="json")}
        )

    async def member_added(
        self, user_ids: Collection[str], *, conversation_id: str, user_id: str, actor_id: str
    ) -> None:
        await self._publish(
            user_ids,
            "member.added",
            {"conversation_id": conversation_id, "user_id": user_id, "actor_id": actor_id},
        )

    async def member_removed(
        self, user_ids: Collection[str], *, conversation_id: str, user_id: str, actor_id: str
    ) -> None:
        await self._publish(
            user_ids,
            "member.removed",
            {"conversation_id": conversation_id, "user_id": user_id, "actor_id": actor_id},
        )

    async def member_role_changed(
        self,
        user_ids: Collection[str],
        *,
        conversation_id: str,
        user_id: str,
        actor_id: str | None,
        role: str,
    ) -> None:
        await self._publish(
            user_ids,
            "member.role_changed",
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "actor_id": actor_id,
                "role": role,
            },
        )

    async def receipt_update(
        self,
        user_ids: Collection[str],
        *,
        conversation_id: str,
        user_id: str,
        delivered_seq: int,
        read_seq: int,
    ) -> None:
        await self._publish(
            user_ids,
            "receipt.update",
            {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "delivered_seq": delivered_seq,
                "read_seq": read_seq,
            },
        )

    async def typing(
        self,
        user_ids: Collection[str],
        *,
        conversation_id: str,
        user_id: str,
        is_typing: bool,
    ) -> None:
        await self._publish(
            user_ids,
            "typing",
            {"conversation_id": conversation_id, "user_id": user_id, "is_typing": is_typing},
        )

    async def presence_update(
        self,
        user_ids: Collection[str],
        *,
        user_id: str,
        online: bool,
        last_seen_at: int | None,
    ) -> None:
        await self._publish(
            user_ids,
            "presence.update",
            {"user_id": user_id, "online": online, "last_seen_at": last_seen_at},
        )

    async def _publish(self, user_ids: Collection[str], event_type: str, payload: dict) -> None:
        if not user_ids:
            return
        try:
            await self._gateway.publish_to_users(user_ids, event_type, payload)
        except Exception:
            # The write already committed; a failed push must never fail the request.
            logger.exception("Failed to publish %s", event_type)
