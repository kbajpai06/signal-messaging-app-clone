import json

from app.models import Conversation, Message
from app.models.enums import MessageType
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.message_repo import MessageRepository
from app.utils.ids import new_id
from app.utils.time import now_ms


class MessageAppender:
    """Single write path for every message, user or system.

    allocate seq -> insert -> update denormalized last_message_* -> advance the author's own
    cursors. Callers own the transaction (commit) and publish events after it.
    """

    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        members: MemberRepository,
        messages: MessageRepository,
    ) -> None:
        self._conversations = conversations
        self._members = members
        self._messages = messages

    async def append(
        self,
        conversation: Conversation,
        *,
        type: MessageType,
        body: str | None,
        sender_id: str | None = None,
        actor_id: str | None = None,
        client_id: str | None = None,
        reply_to_id: str | None = None,
    ) -> Message:
        created_at = now_ms()
        seq = await self._conversations.allocate_seq(conversation)

        expires_at = None
        if type is not MessageType.SYSTEM and conversation.disappearing_ttl_s:
            expires_at = created_at + conversation.disappearing_ttl_s * 1000

        message = await self._messages.insert(
            Message(
                id=new_id(),
                conversation_id=conversation.id,
                seq=seq,
                sender_id=sender_id,
                client_id=client_id,
                type=type.value,
                body=body,
                reply_to_id=reply_to_id,
                created_at=created_at,
                expires_at=expires_at,
            )
        )
        self._conversations.set_last_message(conversation, message)

        # Your own messages are never "unread" for you.
        author_id = sender_id or actor_id
        if author_id:
            await self._members.advance_cursors(conversation.id, author_id, delivered=seq, read=seq)
        return message

    async def append_system(
        self, conversation: Conversation, event: str, *, actor_id: str | None = None, **data: object
    ) -> Message:
        body = json.dumps({"event": event, "actor": actor_id, **data})
        return await self.append(
            conversation, type=MessageType.SYSTEM, body=body, actor_id=actor_id
        )
