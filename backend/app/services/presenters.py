from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from app.models import Contact, Conversation, ConversationMember, Message, User
from app.models.enums import MessageType
from app.schemas.contact import ContactOut
from app.schemas.conversation import ConversationDetailOut, ConversationListItemOut, MemberOut
from app.schemas.message import (
    MessageOut,
    MessagePreviewOut,
    MessageStatus,
    ReplyPreviewOut,
)
from app.schemas.user import UserDirectoryEntry

OnlineCheck = Callable[[str], bool]
MemberRow = tuple[ConversationMember, User]

PREVIEW_MAX_CHARS = 200
REPLY_PREVIEW_MAX_CHARS = 140


@dataclass(frozen=True)
class ReceiptFloor:
    """Lowest delivered/read cursor among everyone except the viewer.

    A message is "read" once every other member has read it. For direct chats
    there is one other member, so the minimum is that member's cursor.
    """

    delivered: int = 0
    read: int = 0

    @classmethod
    def for_viewer(cls, members: Iterable[ConversationMember], viewer_id: str) -> "ReceiptFloor":
        others = [m for m in members if m.user_id != viewer_id]
        if not others:
            return cls()
        return cls(
            delivered=min(m.last_delivered_seq for m in others),
            read=min(m.last_read_seq for m in others),
        )

    def status(self, seq: int) -> MessageStatus:
        if seq <= self.read:
            return "read"
        if seq <= self.delivered:
            return "delivered"
        return "sent"


def own_status(message: Message, viewer_id: str, floor: ReceiptFloor) -> MessageStatus | None:
    return floor.status(message.seq) if message.sender_id == viewer_id else None


def _visible_body(message: Message, limit: int | None) -> str | None:
    if message.deleted_at is not None or message.body is None:
        return None
    # System bodies are JSON; truncating would corrupt them.
    if limit is not None and message.type != MessageType.SYSTEM.value and len(message.body) > limit:
        return message.body[:limit].rstrip() + "…"
    return message.body


def reply_preview(reply: Message | None) -> ReplyPreviewOut | None:
    if reply is None:
        return None
    return ReplyPreviewOut(
        id=reply.id,
        seq=reply.seq,
        sender_id=reply.sender_id,
        type=reply.type,
        body=_visible_body(reply, REPLY_PREVIEW_MAX_CHARS),
    )


def message_out(
    message: Message, *, reply: Message | None = None, status: MessageStatus | None = None
) -> MessageOut:
    return MessageOut(
        id=message.id,
        conversation_id=message.conversation_id,
        seq=message.seq,
        sender_id=message.sender_id,
        client_id=message.client_id,
        type=message.type,
        body=_visible_body(message, None),
        reply_to=reply_preview(reply),
        created_at=message.created_at,
        expires_at=message.expires_at,
        deleted_at=message.deleted_at,
        status=status,
    )


def message_preview(message: Message, status: MessageStatus | None) -> MessagePreviewOut:
    return MessagePreviewOut(
        id=message.id,
        seq=message.seq,
        sender_id=message.sender_id,
        type=message.type,
        body=_visible_body(message, PREVIEW_MAX_CHARS),
        created_at=message.created_at,
        status=status,
    )


def directory_entry(user: User, *, is_contact: bool) -> UserDirectoryEntry:
    entry = UserDirectoryEntry.model_validate(user, from_attributes=True)
    return entry.model_copy(update={"is_contact": is_contact})


def contact_out(contact: Contact, user: User, *, is_online: OnlineCheck) -> ContactOut:
    return ContactOut(
        id=contact.id,
        nickname=contact.nickname,
        created_at=contact.created_at,
        online=is_online(user.id),
        user=directory_entry(user, is_contact=True),
    )


def member_out(member: ConversationMember, user: User, *, is_online: OnlineCheck) -> MemberOut:
    return MemberOut(
        user=user,  # type: ignore[arg-type]  # validated from attributes by UserSummary
        role=member.role,  # type: ignore[arg-type]
        joined_at=member.joined_at,
        online=is_online(user.id),
        last_delivered_seq=member.last_delivered_seq,
        last_read_seq=member.last_read_seq,
    )


def conversation_detail(
    conversation: Conversation, rows: Sequence[MemberRow], *, is_online: OnlineCheck
) -> ConversationDetailOut:
    return ConversationDetailOut(
        id=conversation.id,
        type=conversation.type,  # type: ignore[arg-type]
        name=conversation.name,
        avatar_url=conversation.avatar_url,
        description=conversation.description,
        disappearing_ttl_s=conversation.disappearing_ttl_s,
        created_by=conversation.created_by,
        created_at=conversation.created_at,
        last_seq=conversation.last_seq,
        last_message_at=conversation.last_message_at,
        members=[member_out(m, u, is_online=is_online) for m, u in rows],
    )


def conversation_list_item(
    conversation: Conversation,
    mine: ConversationMember,
    last_message: Message | None,
    rows: Sequence[MemberRow],
    *,
    viewer_id: str,
    is_online: OnlineCheck,
) -> ConversationListItemOut:
    detail = conversation_detail(conversation, rows, is_online=is_online)
    preview = None
    if last_message is not None:
        floor = ReceiptFloor.for_viewer((m for m, _ in rows), viewer_id)
        preview = message_preview(last_message, own_status(last_message, viewer_id, floor))
    return ConversationListItemOut(
        **dict(detail),
        last_message=preview,
        unread_count=max(0, conversation.last_seq - mine.last_read_seq),
        muted_until=mine.muted_until,
        is_archived=mine.is_archived,
    )
