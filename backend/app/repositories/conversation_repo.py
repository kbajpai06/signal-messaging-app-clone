from sqlalchemy import or_, select, update
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import set_committed_value

from app.models import Conversation, ConversationMember, Message, User
from app.models.enums import ConversationType
from app.repositories.base import BaseRepository
from app.utils.ids import new_id
from app.utils.time import now_ms


class ConversationRepository(BaseRepository[Conversation]):
    model = Conversation

    async def get_by_direct_key(self, key: str) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation).where(Conversation.direct_key == key)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        kind: ConversationType,
        created_by: str,
        direct_key: str | None = None,
        name: str | None = None,
        description: str | None = None,
    ) -> Conversation:
        now = now_ms()
        conversation = Conversation(
            id=new_id(),
            type=kind.value,
            direct_key=direct_key,
            name=name,
            description=description,
            created_by=created_by,
            last_seq=0,
            last_message_at=now,
            created_at=now,
        )
        self.add(conversation)
        await self.flush()
        return conversation

    async def allocate_seq(self, conversation: Conversation) -> int:
        """Atomically bump the per-conversation sequence. Must be the first write of the txn."""
        result = await self._session.execute(
            update(Conversation)
            .where(Conversation.id == conversation.id)
            .values(last_seq=Conversation.last_seq + 1)
            .returning(Conversation.last_seq)
            .execution_options(synchronize_session=False)
        )
        seq = result.scalar_one()
        # Keep the in-memory entity current without marking it dirty.
        set_committed_value(conversation, "last_seq", seq)
        return seq

    @staticmethod
    def set_last_message(conversation: Conversation, message: Message) -> None:
        conversation.last_message_id = message.id
        conversation.last_message_at = message.created_at

    async def list_for_user(
        self, user_id: str, query: str | None
    ) -> list[tuple[Conversation, ConversationMember, Message | None]]:
        """Conversation rows + my membership + last message in one query, newest activity first.

        Empty direct chats are hidden (like Signal); groups always show.
        """
        last_message = aliased(Message)
        stmt = (
            select(Conversation, ConversationMember, last_message)
            .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
            .outerjoin(last_message, last_message.id == Conversation.last_message_id)
            .where(
                ConversationMember.user_id == user_id,
                ConversationMember.left_at.is_(None),
                or_(Conversation.type == ConversationType.GROUP.value, Conversation.last_seq > 0),
            )
            .order_by(Conversation.last_message_at.desc(), Conversation.id)
        )

        needle = (query or "").strip()
        if needle:
            peer = aliased(ConversationMember)
            peer_user = aliased(User)
            peer_matches = (
                select(peer.user_id)
                .join(peer_user, peer_user.id == peer.user_id)
                .where(
                    peer.conversation_id == Conversation.id,
                    peer.user_id != user_id,
                    peer.left_at.is_(None),
                    or_(
                        peer_user.display_name.icontains(needle, autoescape=True),
                        peer_user.username.icontains(needle, autoescape=True),
                        peer_user.phone_number.icontains(needle, autoescape=True),
                    ),
                )
                .exists()
            )
            stmt = stmt.where(
                or_(Conversation.name.icontains(needle, autoescape=True), peer_matches)
            )

        rows = (await self._session.execute(stmt)).all()
        return [(conv, mine, last) for conv, mine, last in rows]
