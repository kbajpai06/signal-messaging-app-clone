from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Contact, ConversationMember, User


class PresenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def peer_user_ids(self, user_id: str) -> list[str]:
        """Everyone who may see this user's presence: shared conversations and contacts."""
        my_conversations = select(ConversationMember.conversation_id).where(
            ConversationMember.user_id == user_id, ConversationMember.left_at.is_(None)
        )
        shared = select(ConversationMember.user_id).where(
            ConversationMember.conversation_id.in_(my_conversations),
            ConversationMember.left_at.is_(None),
            ConversationMember.user_id != user_id,
        )
        contacts_out = select(Contact.contact_user_id).where(Contact.owner_id == user_id)
        contacts_in = select(Contact.owner_id).where(Contact.contact_user_id == user_id)
        stmt = shared.union(contacts_out, contacts_in)
        return list((await self._session.scalars(stmt)).all())

    async def set_last_seen(self, user_id: str, at_ms: int) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(last_seen_at=at_ms)
        )
