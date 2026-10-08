from app.core.uow import UnitOfWork
from app.models import User
from app.repositories.member_repo import MemberRepository
from app.services.access import ConversationAccess
from app.services.events import EventPublisher


class ReceiptService:
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

    async def mark_read(self, user: User, conversation_id: str, up_to_seq: int) -> None:
        """Cursor update: one tiny write, monotonic and idempotent. Read implies delivered."""
        conversation, _ = await self._access.require_member(conversation_id, user.id)
        target = min(up_to_seq, conversation.last_seq)

        before = await self._members.cursors(conversation_id, user.id)
        await self._members.advance_cursors(conversation_id, user.id, delivered=target, read=target)
        await self._uow.commit()
        after = await self._members.cursors(conversation_id, user.id)

        if after != before:
            recipients = await self._members.active_user_ids(conversation_id)
            await self._events.receipt_update(
                recipients,
                conversation_id=conversation_id,
                user_id=user.id,
                delivered_seq=after[0],
                read_seq=after[1],
            )
