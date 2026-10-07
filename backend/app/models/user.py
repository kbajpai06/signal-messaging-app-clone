from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.utils.ids import new_id
from app.utils.time import now_ms


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_id)
    phone_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, unique=True)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    about: Mapped[str | None] = mapped_column(String)
    avatar_url: Mapped[str | None] = mapped_column(String)
    avatar_color: Mapped[str] = mapped_column(String, nullable=False)
    last_seen_at: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[int] = mapped_column(Integer, nullable=False, default=now_ms)
