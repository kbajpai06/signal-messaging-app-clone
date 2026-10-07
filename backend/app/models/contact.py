from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.ids import new_id
from app.utils.time import now_ms


class Contact(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        UniqueConstraint("owner_id", "contact_user_id", name="uq_contacts_owner_contact"),
        CheckConstraint("owner_id <> contact_user_id", name="ck_contacts_not_self"),
        Index("ix_contacts_owner_id", "owner_id"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    owner_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    contact_user_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    nickname: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
