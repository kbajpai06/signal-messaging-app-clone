from collections.abc import Collection

from sqlalchemy import func, select, update

from app.models import ConversationMember, User
from app.models.enums import MemberRole


class MemberRepository:
    """Membership and receipt cursors. Composite PK, so it does not extend BaseRepository."""

    def __init__(self, session) -> None:
        self._session = session

    async def get(self, conversation_id: str, user_id: str) -> ConversationMember | None:
        return await self._session.get(ConversationMember, (conversation_id, user_id))

    async def join(
        self, *, conversation_id: str, user_id: str, role: MemberRole, joined_at: int
    ) -> ConversationMember:
        """Create a membership, or reactivate a previously-left one."""
        member = await self.get(conversation_id, user_id)
        if member is None:
            member = ConversationMember(
                conversation_id=conversation_id,
                user_id=user_id,
                role=role.value,
                joined_at=joined_at,
            )
            self._session.add(member)
        else:
            member.left_at = None
            member.role = role.value
            member.joined_at = joined_at
        await self._session.flush()
        return member

    async def list_active(self, conversation_id: str) -> list[tuple[ConversationMember, User]]:
        return await self.list_active_for_conversations([conversation_id])

    async def list_active_for_conversations(
        self, conversation_ids: Collection[str]
    ) -> list[tuple[ConversationMember, User]]:
        if not conversation_ids:
            return []
        stmt = (
            select(ConversationMember, User)
            .join(User, User.id == ConversationMember.user_id)
            .where(
                ConversationMember.conversation_id.in_(conversation_ids),
                ConversationMember.left_at.is_(None),
            )
            .order_by(ConversationMember.joined_at, ConversationMember.user_id)
            # Cursor updates are bulk SQL; force fresh values over any stale identity-map entry.
            .execution_options(populate_existing=True)
        )
        return [(member, user) for member, user in (await self._session.execute(stmt)).all()]

    async def active_user_ids(self, conversation_id: str) -> list[str]:
        stmt = select(ConversationMember.user_id).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.left_at.is_(None),
        )
        return list((await self._session.scalars(stmt)).all())

    async def count_active_admins(self, conversation_id: str) -> int:
        stmt = (
            select(func.count())
            .select_from(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.role == MemberRole.ADMIN.value,
                ConversationMember.left_at.is_(None),
            )
        )
        return int(await self._session.scalar(stmt) or 0)

    async def oldest_active_member(
        self, conversation_id: str, *, excluding: str
    ) -> ConversationMember | None:
        stmt = (
            select(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id != excluding,
                ConversationMember.left_at.is_(None),
            )
            .order_by(ConversationMember.joined_at, ConversationMember.user_id)
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def cursors(self, conversation_id: str, user_id: str) -> tuple[int, int]:
        """(last_delivered_seq, last_read_seq). Column select, so never stale."""
        stmt = select(
            ConversationMember.last_delivered_seq, ConversationMember.last_read_seq
        ).where(
            ConversationMember.conversation_id == conversation_id,
            ConversationMember.user_id == user_id,
        )
        row = (await self._session.execute(stmt)).one()
        return row[0], row[1]

    async def advance_cursors(
        self,
        conversation_id: str,
        user_id: str,
        *,
        delivered: int | None = None,
        read: int | None = None,
    ) -> None:
        """Monotonic (SQL MAX) cursor update: one tiny write, idempotent, race-safe."""
        values = _cursor_values(delivered, read)
        if not values:
            return
        await self._session.execute(
            update(ConversationMember)
            .where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
            .values(**values)
            .execution_options(synchronize_session=False)
        )

    async def advance_all_cursors(self, conversation_id: str, seq: int) -> None:
        await self._session.execute(
            update(ConversationMember)
            .where(ConversationMember.conversation_id == conversation_id)
            .values(**_cursor_values(seq, seq))
            .execution_options(synchronize_session=False)
        )


def _cursor_values(delivered: int | None, read: int | None) -> dict:
    values: dict = {}
    if delivered is not None:
        values["last_delivered_seq"] = func.max(ConversationMember.last_delivered_seq, delivered)
    if read is not None:
        values["last_read_seq"] = func.max(ConversationMember.last_read_seq, read)
    return values
