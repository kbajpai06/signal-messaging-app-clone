from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import MemberRole, sql_in
from app.utils.time import now_ms


class ConversationMember(Base):
    """Membership + per-member receipt cursors. Covers direct chats too."""

    __tablename__ = "conversation_members"
    __table_args__ = (
        CheckConstraint(sql_in("role", MemberRole), name="ck_members_role"),
        Index("ix_members_user_left", "user_id", "left_at"),
    )

    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default=MemberRole.MEMBER.value)
    joined_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
    # Soft removal keeps history and enables "X left" system messages.
    left_at: Mapped[int | None] = mapped_column(Integer)
    # Receipt cursors: one tiny write marks N messages delivered/read.
    last_delivered_seq: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    last_read_seq: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )
    muted_until: Mapped[int | None] = mapped_column(Integer)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("0")
    )
