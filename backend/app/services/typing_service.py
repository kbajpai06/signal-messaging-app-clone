from app.models import User
from app.repositories.member_repo import MemberRepository
from app.services.access import ConversationAccess
from app.services.events import EventPublisher


class TypingService:
    """Typing is relayed to the other active members and never stored."""

    def __init__(
        self, *, access: ConversationAccess, members: MemberRepository, events: EventPublisher
    ) -> None:
        self._access = access
        self._members = members
        self._events = events

    async def relay(self, user: User, conversation_id: str, *, is_typing: bool) -> None:
        await self._access.require_member(conversation_id, user.id)
        member_ids = await self._members.active_user_ids(conversation_id)
        others = [uid for uid in member_ids if uid != user.id]
        await self._events.typing(
            others, conversation_id=conversation_id, user_id=user.id, is_typing=is_typing
        )
