from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import ConversationType, sql_in
from app.utils.ids import new_id
from app.utils.time import now_ms


class Conversation(Base):
    """Unified table for direct and group conversations."""

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint(sql_in("type", ConversationType), name="ck_conversations_type"),
        CheckConstraint(
            "(type = 'direct' AND direct_key IS NOT NULL)"
            " OR (type = 'group' AND direct_key IS NULL)",
            name="ck_conversations_direct_key",
        ),
        Index("ix_conversations_last_message_at", "last_message_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    type: Mapped[str] = mapped_column(String, nullable=False)
    # "{minUserId}:{maxUserId}" for DMs. UNIQUE makes get-or-create atomic.
    direct_key: Mapped[str | None] = mapped_column(String, unique=True)
    name: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(String)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    # Sequence allocator: UPDATE ... SET last_seq = last_seq + 1 RETURNING last_seq
    last_seq: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    # Denormalized for the list preview. Deliberately NOT a FK (avoids a circular FK with
    # messages; SQLite cannot ALTER ADD CONSTRAINT). The service layer keeps it consistent.
    last_message_id: Mapped[str | None] = mapped_column(String)
    last_message_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
    disappearing_ttl_s: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
