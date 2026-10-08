from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.models import Conversation, ConversationMember
from app.models.enums import ConversationType, MemberRole
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository


class ConversationAccess:
    """Centralized membership / admin checks, so no service re-implements them."""

    def __init__(self, *, conversations: ConversationRepository, members: MemberRepository) -> None:
        self._conversations = conversations
        self._members = members

    async def require_member(
        self, conversation_id: str, user_id: str
    ) -> tuple[Conversation, ConversationMember]:
        conversation = await self._conversations.get(conversation_id)
        if conversation is None:
            raise NotFoundError("Conversation not found", code="conversation_not_found")
        member = await self._members.get(conversation_id, user_id)
        if member is None or member.left_at is not None:
            raise ForbiddenError("You are not a member of this conversation", code="not_a_member")
        return conversation, member

    async def require_group_member(
        self, conversation_id: str, user_id: str
    ) -> tuple[Conversation, ConversationMember]:
        conversation, member = await self.require_member(conversation_id, user_id)
        if conversation.type != ConversationType.GROUP.value:
            raise AppError("This action only applies to groups", code="not_a_group")
        return conversation, member

    async def require_group_admin(
        self, conversation_id: str, user_id: str
    ) -> tuple[Conversation, ConversationMember]:
        conversation, member = await self.require_group_member(conversation_id, user_id)
        if member.role != MemberRole.ADMIN.value:
            raise ForbiddenError("Only group admins can do that", code="admin_required")
        return conversation, member
