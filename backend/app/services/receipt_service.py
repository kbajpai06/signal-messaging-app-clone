from app.core.uow import UnitOfWork
from app.models import User
from app.repositories.member_repo import MemberRepository
from app.services.access import ConversationAccess
from app.services.events import EventPublisher


class ReceiptService:
    """Cursor-based receipts: every operation is one tiny, monotonic, idempotent write."""

    def __init__(
        self,
        *,
        members: MemberRepository,
        access: ConversationAccess,
        events: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._members = members
        self._access = access
        self._events = events
        self._uow = uow

    async def mark_delivered(self, user: User, conversation_id: str, up_to_seq: int) -> None:
        conversation, _ = await self._access.require_member(conversation_id, user.id)
        target = min(up_to_seq, conversation.last_seq)
        await self._advance(user.id, conversation_id, delivered=target)

    async def mark_read(self, user: User, conversation_id: str, up_to_seq: int) -> None:
        """Read implies delivered."""
        conversation, _ = await self._access.require_member(conversation_id, user.id)
        target = min(up_to_seq, conversation.last_seq)
        await self._advance(user.id, conversation_id, delivered=target, read=target)

    async def deliver_pending(self, user: User) -> None:
        """On (re)connect: everything sent while offline is now delivered. One transaction."""
        pending = await self._members.undelivered(user.id)
        if not pending:
            return
        for conversation_id, last_seq in pending:
            await self._members.advance_cursors(conversation_id, user.id, delivered=last_seq)
        await self._uow.commit()
        for conversation_id, _ in pending:
            await self._publish_cursors(conversation_id, user.id)

    async def _advance(
        self,
        user_id: str,
        conversation_id: str,
        *,
        delivered: int | None = None,
        read: int | None = None,
    ) -> None:
        before = await self._members.cursors(conversation_id, user_id)
        await self._members.advance_cursors(
            conversation_id, user_id, delivered=delivered, read=read
        )
        await self._uow.commit()
        if await self._members.cursors(conversation_id, user_id) != before:
            await self._publish_cursors(conversation_id, user_id)

    async def _publish_cursors(self, conversation_id: str, user_id: str) -> None:
        delivered, read = await self._members.cursors(conversation_id, user_id)
        recipients = await self._members.active_user_ids(conversation_id)
        await self._events.receipt_update(
            recipients,
            conversation_id=conversation_id,
            user_id=user_id,
            delivered_seq=delivered,
            read_seq=read,
        )
