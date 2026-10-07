from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.ids import new_id
from app.utils.time import now_ms


class UserSession(Base):
    """A login session. The JWT carries its id (`sid`); logout sets `revoked_at`."""

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    device_label: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
    expires_at: Mapped[int] = mapped_column(Integer, nullable=False)
    revoked_at: Mapped[int | None] = mapped_column(Integer)
