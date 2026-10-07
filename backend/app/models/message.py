from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.enums import MessageType, sql_in
from app.utils.ids import new_id
from app.utils.time import now_ms


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        # Backbone of ordering/dedup/sync. Also serves "history newest-first" via reverse scan.
        UniqueConstraint("conversation_id", "seq", name="uq_messages_conversation_seq"),
        # Idempotent sends. NULL client_ids (system/seed) are distinct in SQLite.
        UniqueConstraint("sender_id", "client_id", name="uq_messages_sender_client"),
        CheckConstraint(sql_in("type", MessageType), name="ck_messages_type"),
        Index(
            "ix_messages_expires_at",
            "expires_at",
            sqlite_where=text("expires_at IS NOT NULL"),
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL for system messages.
    sender_id: Mapped[str | None] = mapped_column(String, ForeignKey("users.id"))
    client_id: Mapped[str | None] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, nullable=False, default=MessageType.TEXT.value)
    # System events store JSON, e.g. {"event": "member_added", "actor": ..., "target": ...}
    body: Mapped[str | None] = mapped_column(Text)
    reply_to_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("messages.id", ondelete="SET NULL")
    )
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
    expires_at: Mapped[int | None] = mapped_column(Integer)
    deleted_at: Mapped[int | None] = mapped_column(Integer)
