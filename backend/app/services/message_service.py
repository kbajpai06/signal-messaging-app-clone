from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.uow import UnitOfWork
from app.models import Message, User
from app.models.enums import MessageType
from app.repositories.member_repo import MemberRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.message import MessageOut, MessagePageOut, SendMessageIn
from app.services import presenters
from app.services.access import ConversationAccess
from app.services.events import EventPublisher
from app.services.message_appender import MessageAppender
from app.services.presenters import ReceiptFloor
from app.utils.time import now_ms


class MessageService:
    def __init__(
        self,
        *,
        messages: MessageRepository,
        members: MemberRepository,
        access: ConversationAccess,
        appender: MessageAppender,
        events: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._messages = messages
        self._members = members
        self._access = access
        self._appender = appender
        self._events = events
        self._uow = uow

    async def history(
        self,
        user: User,
        conversation_id: str,
        *,
        before_seq: int | None,
        after_seq: int | None,
        limit: int,
    ) -> MessagePageOut:
        if before_seq is not None and after_seq is not None:
            raise AppError("Use either before_seq or after_seq, not both", code="invalid_cursor")
        await self._access.require_member(conversation_id, user.id)

        # Fetch one extra row to learn whether more pages exist.
        rows = await self._messages.page(
            conversation_id,
            before_seq=before_seq,
            after_seq=after_seq,
            limit=limit + 1,
            now=now_ms(),
        )
        has_more = len(rows) > limit
        rows = rows[:limit]
        if after_seq is None:
            rows.reverse()  # fetched newest-first; the API always returns ascending seq

        member_rows = await self._members.list_active(conversation_id)
        floor = ReceiptFloor.for_viewer((m for m, _ in member_rows), user.id)
        items = [
            presenters.message_out(
                message, reply=replied, status=presenters.own_status(message, user.id, floor)
            )
            for message, replied in rows
        ]
        return MessagePageOut(items=items, has_more=has_more)

    async def send(
        self, user: User, conversation_id: str, data: SendMessageIn
    ) -> tuple[MessageOut, bool]:
        """Idempotent send (REST fallback). Returns (message, created)."""
        conversation, _ = await self._access.require_member(conversation_id, user.id)

        existing = await self._messages.get_by_client_id(user.id, data.client_id)
        if existing is not None:
            return await self._present_existing(existing, conversation_id, user.id), False

        reply: Message | None = None
        if data.reply_to_id:
            reply = await self._messages.get_in_conversation(conversation_id, data.reply_to_id)
            if reply is None:
                raise NotFoundError(
                    "The message you replied to was not found", code="reply_not_found"
                )

        try:
            message = await self._appender.append(
                conversation,
                type=MessageType.TEXT,
                body=data.body,
                sender_id=user.id,
                client_id=data.client_id,
                reply_to_id=reply.id if reply else None,
            )
            await self._uow.commit()
        except IntegrityError:
            # Same client_id raced in on another request: return the winner, never a duplicate.
            await self._uow.rollback()
            winner = await self._messages.get_by_client_id(user.id, data.client_id)
            if winner is None:
                raise
            return await self._present_existing(winner, conversation_id, user.id), False

        out = presenters.message_out(message, reply=reply, status="sent")
        recipients = await self._members.active_user_ids(conversation_id)
        await self._events.message_new(recipients, out)
        return out, True

    async def _present_existing(
        self, message: Message, conversation_id: str, viewer_id: str
    ) -> MessageOut:
        if message.conversation_id != conversation_id:
            raise ConflictError(
                "That client_id was already used elsewhere", code="client_id_conflict"
            )
        reply = await self._messages.get(message.reply_to_id) if message.reply_to_id else None
        member_rows = await self._members.list_active(conversation_id)
        floor = ReceiptFloor.for_viewer((m for m, _ in member_rows), viewer_id)
        return presenters.message_out(
            message, reply=reply, status=presenters.own_status(message, viewer_id, floor)
        )
