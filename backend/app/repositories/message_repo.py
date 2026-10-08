from sqlalchemy import or_, select
from sqlalchemy.orm import aliased

from app.models import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    model = Message

    async def insert(self, message: Message) -> Message:
        self.add(message)
        await self.flush()
        return message

    async def get_by_client_id(self, sender_id: str, client_id: str) -> Message | None:
        result = await self._session.execute(
            select(Message).where(Message.sender_id == sender_id, Message.client_id == client_id)
        )
        return result.scalar_one_or_none()

    async def get_in_conversation(self, conversation_id: str, message_id: str) -> Message | None:
        result = await self._session.execute(
            select(Message).where(
                Message.id == message_id, Message.conversation_id == conversation_id
            )
        )
        return result.scalar_one_or_none()

    async def page(
        self,
        conversation_id: str,
        *,
        before_seq: int | None,
        after_seq: int | None,
        limit: int,
        now: int,
    ) -> list[tuple[Message, Message | None]]:
        """Keyset page with the replied-to message joined in.

        after_seq: ascending, seq > after_seq (gap fill / sync).
        otherwise: descending from before_seq (or the tail). The caller reverses it.
        """
        reply = aliased(Message)
        stmt = (
            select(Message, reply)
            .outerjoin(reply, reply.id == Message.reply_to_id)
            .where(
                Message.conversation_id == conversation_id,
                or_(Message.expires_at.is_(None), Message.expires_at > now),
            )
        )
        if after_seq is not None:
            stmt = stmt.where(Message.seq > after_seq).order_by(Message.seq.asc())
        else:
            if before_seq is not None:
                stmt = stmt.where(Message.seq < before_seq)
            stmt = stmt.order_by(Message.seq.desc())
        rows = (await self._session.execute(stmt.limit(limit))).all()
        return [(message, replied) for message, replied in rows]
