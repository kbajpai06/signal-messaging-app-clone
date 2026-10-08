from collections import defaultdict
from collections.abc import Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.core.uow import UnitOfWork
from app.models import Conversation, ConversationMember, User
from app.models.enums import ConversationType, MemberRole
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.user_repo import UserRepository
from app.schemas.conversation import ConversationDetailOut, ConversationListItemOut
from app.services import presenters
from app.services.access import ConversationAccess
from app.services.events import EventPublisher
from app.services.message_appender import MessageAppender
from app.utils.ids import direct_key
from app.utils.time import now_ms

PATCHABLE_FIELDS = frozenset({"name", "description", "disappearing_ttl_s"})


class ConversationService:
    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        members: MemberRepository,
        users: UserRepository,
        access: ConversationAccess,
        appender: MessageAppender,
        events: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._conversations = conversations
        self._members = members
        self._users = users
        self._access = access
        self._appender = appender
        self._events = events
        self._uow = uow

    async def list_for_user(self, user: User, query: str | None) -> list[ConversationListItemOut]:
        rows = await self._conversations.list_for_user(user.id, query)
        if not rows:
            return []

        member_rows = await self._members.list_active_for_conversations([c.id for c, _, _ in rows])
        by_conversation: dict[str, list[tuple[ConversationMember, User]]] = defaultdict(list)
        for member, member_user in member_rows:
            by_conversation[member.conversation_id].append((member, member_user))

        return [
            presenters.conversation_list_item(
                conversation,
                mine,
                last_message,
                by_conversation[conversation.id],
                viewer_id=user.id,
                is_online=self._events.is_online,
            )
            for conversation, mine, last_message in rows
        ]

    async def get_detail(self, user: User, conversation_id: str) -> ConversationDetailOut:
        conversation, _ = await self._access.require_member(conversation_id, user.id)
        return await self._detail(conversation)

    async def get_or_create_direct(
        self, user: User, target_user_id: str
    ) -> tuple[ConversationDetailOut, bool]:
        if target_user_id == user.id:
            raise AppError("You cannot start a conversation with yourself", code="invalid_target")
        target = await self._users.get(target_user_id)
        if target is None:
            raise NotFoundError("User not found", code="user_not_found")

        key = direct_key(user.id, target.id)
        conversation = await self._conversations.get_by_direct_key(key)
        created = False
        if conversation is None:
            try:
                conversation = await self._conversations.create(
                    kind=ConversationType.DIRECT, created_by=user.id, direct_key=key
                )
                joined_at = now_ms()
                for member_id in (user.id, target.id):
                    await self._members.join(
                        conversation_id=conversation.id,
                        user_id=member_id,
                        role=MemberRole.MEMBER,
                        joined_at=joined_at,
                    )
                await self._uow.commit()
                created = True
            except IntegrityError:
                # Concurrent get-or-create: the UNIQUE direct_key made us lose, so use the winner.
                await self._uow.rollback()
                conversation = await self._conversations.get_by_direct_key(key)
                if conversation is None:
                    raise
        return await self._detail(conversation), created

    async def update(
        self, user: User, conversation_id: str, changes: Mapping[str, Any]
    ) -> ConversationDetailOut:
        conversation, member = await self._access.require_member(conversation_id, user.id)
        changes = {k: v for k, v in changes.items() if k in PATCHABLE_FIELDS}

        if conversation.type == ConversationType.GROUP.value:
            if member.role != MemberRole.ADMIN.value:
                raise ForbiddenError("Only group admins can do that", code="admin_required")
        elif set(changes) - {"disappearing_ttl_s"}:
            raise AppError(
                "Only disappearing messages can be changed in a direct chat", code="not_a_group"
            )

        system_messages = []
        if "name" in changes and changes["name"] != conversation.name:
            conversation.name = changes["name"]
            system_messages.append(
                await self._appender.append_system(
                    conversation, "group_renamed", actor_id=user.id, name=conversation.name
                )
            )
        if "description" in changes:
            conversation.description = changes["description"]
        if (
            "disappearing_ttl_s" in changes
            and changes["disappearing_ttl_s"] != conversation.disappearing_ttl_s
        ):
            conversation.disappearing_ttl_s = changes["disappearing_ttl_s"]
            system_messages.append(
                await self._appender.append_system(
                    conversation,
                    "disappearing_changed",
                    actor_id=user.id,
                    ttl_s=conversation.disappearing_ttl_s,
                )
            )
        await self._uow.commit()

        rows = await self._members.list_active(conversation.id)
        detail = presenters.conversation_detail(
            conversation, rows, is_online=self._events.is_online
        )
        recipients = [m.user_id for m, _ in rows]
        await self._events.conversation_updated(recipients, detail)
        for message in system_messages:
            await self._events.message_new(recipients, presenters.message_out(message))
        return detail

    async def _detail(self, conversation: Conversation) -> ConversationDetailOut:
        rows = await self._members.list_active(conversation.id)
        return presenters.conversation_detail(conversation, rows, is_online=self._events.is_online)
