from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.uow import UnitOfWork
from app.models import Conversation, User
from app.models.enums import ConversationType, MemberRole
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.user_repo import UserRepository
from app.schemas.conversation import ConversationDetailOut
from app.services import presenters
from app.services.access import ConversationAccess
from app.services.avatar_service import AvatarService
from app.services.events import EventPublisher
from app.services.message_appender import MessageAppender
from app.utils.time import now_ms

MAX_GROUP_MEMBERS = 100


class GroupService:
    def __init__(
        self,
        *,
        conversations: ConversationRepository,
        members: MemberRepository,
        users: UserRepository,
        access: ConversationAccess,
        appender: MessageAppender,
        avatars: AvatarService,
        events: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._conversations = conversations
        self._members = members
        self._users = users
        self._access = access
        self._appender = appender
        self._avatars = avatars
        self._events = events
        self._uow = uow

    async def create_group(
        self, user: User, *, name: str, member_ids: list[str], description: str | None
    ) -> ConversationDetailOut:
        others = _unique_others(member_ids, user.id)
        if not others:
            raise AppError("Add at least one other member", code="members_required")
        if len(others) + 1 > MAX_GROUP_MEMBERS:
            raise AppError(f"Groups are limited to {MAX_GROUP_MEMBERS} members", code="group_full")
        await self._require_users_exist(others)

        conversation = await self._conversations.create(
            kind=ConversationType.GROUP,
            created_by=user.id,
            name=name,
            description=description,
        )
        joined_at = now_ms()
        await self._members.join(
            conversation_id=conversation.id,
            user_id=user.id,
            role=MemberRole.ADMIN,
            joined_at=joined_at,
        )
        for member_id in others:
            await self._members.join(
                conversation_id=conversation.id,
                user_id=member_id,
                role=MemberRole.MEMBER,
                joined_at=joined_at,
            )
        created = await self._appender.append_system(
            conversation, "group_created", actor_id=user.id
        )
        # Everyone starts caught up, so the creation notice never shows as unread.
        await self._members.advance_all_cursors(conversation.id, created.seq)
        await self._uow.commit()

        detail, recipients = await self._detail_and_recipients(conversation)
        await self._events.conversation_updated(recipients, detail)
        await self._events.message_new(recipients, presenters.message_out(created))
        return detail

    async def add_members(
        self, user: User, conversation_id: str, user_ids: list[str]
    ) -> ConversationDetailOut:
        conversation, _ = await self._access.require_group_admin(conversation_id, user.id)
        requested = _unique_others(user_ids, user.id)
        if not requested:
            raise AppError("Choose at least one person to add", code="members_required")
        await self._require_users_exist(requested)

        already_active = set(await self._members.active_user_ids(conversation.id))
        new_ids = [uid for uid in requested if uid not in already_active]
        if not new_ids:
            return (await self._detail_and_recipients(conversation))[0]  # idempotent no-op
        if len(already_active) + len(new_ids) > MAX_GROUP_MEMBERS:
            raise AppError(f"Groups are limited to {MAX_GROUP_MEMBERS} members", code="group_full")

        system_messages = []
        for new_id_ in new_ids:
            await self._members.join(
                conversation_id=conversation.id,
                user_id=new_id_,
                role=MemberRole.MEMBER,
                joined_at=now_ms(),
            )
            system_messages.append(
                await self._appender.append_system(
                    conversation, "member_added", actor_id=user.id, target=new_id_
                )
            )
        # Newcomers start caught up with the notices about their own arrival.
        last_seq = system_messages[-1].seq
        for new_id_ in new_ids:
            await self._members.advance_cursors(
                conversation.id, new_id_, delivered=last_seq, read=last_seq
            )
        await self._uow.commit()

        detail, recipients = await self._detail_and_recipients(conversation)
        await self._events.conversation_updated(recipients, detail)
        for new_id_ in new_ids:
            await self._events.member_added(
                recipients, conversation_id=conversation.id, user_id=new_id_, actor_id=user.id
            )
        for message in system_messages:
            await self._events.message_new(recipients, presenters.message_out(message))
        return detail

    async def remove_member(
        self, user: User, conversation_id: str, target_user_id: str
    ) -> ConversationDetailOut:
        conversation, _ = await self._access.require_group_admin(conversation_id, user.id)
        if target_user_id == user.id:
            raise AppError("Use leave to exit the group", code="use_leave")
        target = await self._members.get(conversation.id, target_user_id)
        if target is None or target.left_at is not None:
            raise NotFoundError("Member not found", code="member_not_found")

        target.left_at = now_ms()
        message = await self._appender.append_system(
            conversation, "member_removed", actor_id=user.id, target=target_user_id
        )
        await self._uow.commit()

        detail, remaining = await self._detail_and_recipients(conversation)
        await self._events.member_removed(
            [*remaining, target_user_id],
            conversation_id=conversation.id,
            user_id=target_user_id,
            actor_id=user.id,
        )
        await self._events.conversation_updated(remaining, detail)
        await self._events.message_new(remaining, presenters.message_out(message))
        return detail

    async def change_role(
        self, user: User, conversation_id: str, target_user_id: str, role: MemberRole
    ) -> ConversationDetailOut:
        conversation, _ = await self._access.require_group_admin(conversation_id, user.id)
        target = await self._members.get(conversation.id, target_user_id)
        if target is None or target.left_at is not None:
            raise NotFoundError("Member not found", code="member_not_found")
        if target.role == role.value:
            return (await self._detail_and_recipients(conversation))[0]  # idempotent no-op

        if (
            role is MemberRole.MEMBER
            and await self._members.count_active_admins(conversation.id) <= 1
        ):
            raise ConflictError("A group needs at least one admin", code="last_admin")

        target.role = role.value
        message = await self._appender.append_system(
            conversation,
            "member_role_changed",
            actor_id=user.id,
            target=target_user_id,
            role=role.value,
        )
        await self._uow.commit()

        detail, recipients = await self._detail_and_recipients(conversation)
        await self._events.member_role_changed(
            recipients,
            conversation_id=conversation.id,
            user_id=target_user_id,
            actor_id=user.id,
            role=role.value,
        )
        await self._events.conversation_updated(recipients, detail)
        await self._events.message_new(recipients, presenters.message_out(message))
        return detail

    async def leave(self, user: User, conversation_id: str) -> None:
        conversation, me = await self._access.require_group_member(conversation_id, user.id)
        me.left_at = now_ms()

        successor = None
        if (
            me.role == MemberRole.ADMIN.value
            and await self._members.count_active_admins(conversation.id) == 0
        ):
            # Last admin is leaving: hand the group to the longest-standing member.
            successor = await self._members.oldest_active_member(conversation.id, excluding=user.id)
            if successor is not None:
                successor.role = MemberRole.ADMIN.value

        system_messages = [
            await self._appender.append_system(conversation, "member_left", actor_id=user.id)
        ]
        if successor is not None:
            system_messages.append(
                await self._appender.append_system(
                    conversation,
                    "member_role_changed",
                    target=successor.user_id,
                    role=MemberRole.ADMIN.value,
                )
            )
        await self._uow.commit()

        detail, remaining = await self._detail_and_recipients(conversation)
        await self._events.member_removed(
            [*remaining, user.id],
            conversation_id=conversation.id,
            user_id=user.id,
            actor_id=user.id,
        )
        if successor is not None:
            await self._events.member_role_changed(
                remaining,
                conversation_id=conversation.id,
                user_id=successor.user_id,
                actor_id=None,
                role=MemberRole.ADMIN.value,
            )
        await self._events.conversation_updated(remaining, detail)
        for message in system_messages:
            await self._events.message_new(remaining, presenters.message_out(message))

    async def set_avatar(
        self, user: User, conversation_id: str, data: bytes
    ) -> ConversationDetailOut:
        conversation, _ = await self._access.require_group_admin(conversation_id, user.id)
        new_url = await self._avatars.store(data)
        previous_url = conversation.avatar_url
        conversation.avatar_url = new_url
        try:
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            await self._avatars.discard(new_url)
            raise
        await self._avatars.discard(previous_url)

        detail, recipients = await self._detail_and_recipients(conversation)
        await self._events.conversation_updated(recipients, detail)
        return detail

    async def _require_users_exist(self, user_ids: list[str]) -> None:
        found = await self._users.get_many(user_ids)
        if len(found) != len(user_ids):
            raise NotFoundError("One or more users do not exist", code="user_not_found")

    async def _detail_and_recipients(
        self, conversation: Conversation
    ) -> tuple[ConversationDetailOut, list[str]]:
        rows = await self._members.list_active(conversation.id)
        detail = presenters.conversation_detail(
            conversation, rows, is_online=self._events.is_online
        )
        return detail, [m.user_id for m, _ in rows]


def _unique_others(user_ids: list[str], self_id: str) -> list[str]:
    return list(dict.fromkeys(uid for uid in user_ids if uid != self_id))
