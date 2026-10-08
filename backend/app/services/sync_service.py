from collections import defaultdict
from collections.abc import Mapping

from app.models import ConversationMember, User
from app.repositories.member_repo import MemberRepository
from app.repositories.message_repo import MessageRepository
from app.schemas.message import MessageOut
from app.schemas.sync import ReceiptStateOut, SyncResultOut
from app.services import presenters
from app.services.presenters import ReceiptFloor
from app.utils.time import now_ms

SYNC_MAX_CONVERSATIONS = 100
SYNC_PER_CONVERSATION = 100


class SyncService:
    """Reconnect catch-up: replay what the client missed, plus current receipt cursors."""

    def __init__(self, *, messages: MessageRepository, members: MemberRepository) -> None:
        self._messages = messages
        self._members = members

    async def catch_up(self, user: User, cursors: Mapping[str, int]) -> SyncResultOut:
        active = set(await self._members.active_conversation_ids(user.id))
        # Ids the user is not an active member of are ignored silently.
        requested = [cid for cid in cursors if cid in active]
        selected = requested[:SYNC_MAX_CONVERSATIONS]
        truncated = requested[SYNC_MAX_CONVERSATIONS:]
        if not selected:
            return SyncResultOut(messages=[], receipts=[], truncated=truncated)

        members_by_conversation: dict[str, list[ConversationMember]] = defaultdict(list)
        for member, _ in await self._members.list_active_for_conversations(selected):
            members_by_conversation[member.conversation_id].append(member)

        now = now_ms()
        messages: list[MessageOut] = []
        receipts: list[ReceiptStateOut] = []
        for conversation_id in selected:
            rows = await self._messages.page(
                conversation_id,
                before_seq=None,
                after_seq=cursors[conversation_id],
                limit=SYNC_PER_CONVERSATION + 1,
                now=now,
            )
            if len(rows) > SYNC_PER_CONVERSATION:
                truncated.append(conversation_id)
                rows = rows[:SYNC_PER_CONVERSATION]

            members = members_by_conversation[conversation_id]
            floor = ReceiptFloor.for_viewer(members, user.id)
            messages.extend(
                presenters.message_out(
                    message,
                    reply=replied,
                    status=presenters.own_status(message, user.id, floor),
                )
                for message, replied in rows
            )
            receipts.extend(
                ReceiptStateOut(
                    conversation_id=conversation_id,
                    user_id=m.user_id,
                    delivered_seq=m.last_delivered_seq,
                    read_seq=m.last_read_seq,
                )
                for m in members
            )
        return SyncResultOut(messages=messages, receipts=receipts, truncated=truncated)
