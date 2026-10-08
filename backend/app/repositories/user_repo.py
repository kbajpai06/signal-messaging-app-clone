import re
from collections.abc import Collection

from sqlalchemy import func, or_, select

from app.models.user import User
from app.repositories.base import BaseRepository
from app.utils.avatar import avatar_color_for
from app.utils.ids import new_id
from app.utils.time import now_ms

_PHONE_NOISE = re.compile(r"[\s\-().]")
_PHONE_LIKE = re.compile(r"^\+?[0-9]{3,}$")


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_phone(self, phone_number: str) -> User | None:
        result = await self._session.execute(select(User).where(User.phone_number == phone_number))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self._session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_many(self, ids: Collection[str]) -> list[User]:
        if not ids:
            return []
        result = await self._session.scalars(select(User).where(User.id.in_(ids)))
        return list(result)

    async def search(self, query: str, *, exclude_id: str, limit: int) -> list[User]:
        """Match display name, username or phone number (case-insensitive, substring)."""
        needle = query.strip().lstrip("@")
        if not needle:
            return []
        conditions = [
            User.display_name.icontains(needle, autoescape=True),
            User.username.icontains(needle, autoescape=True),
        ]
        digits = _PHONE_NOISE.sub("", query.strip())
        if _PHONE_LIKE.match(digits):
            conditions.append(User.phone_number.contains(digits, autoescape=True))

        stmt = (
            select(User)
            .where(User.id != exclude_id, or_(*conditions))
            .order_by(func.lower(User.display_name), User.id)
            .limit(limit)
        )
        return list((await self._session.scalars(stmt)).all())

    async def create(self, *, phone_number: str, display_name: str) -> User:
        user_id = new_id()
        user = User(
            id=user_id,
            phone_number=phone_number,
            display_name=display_name,
            avatar_color=avatar_color_for(user_id),
            created_at=now_ms(),
        )
        self.add(user)
        await self.flush()
        return user
