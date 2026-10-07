from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository
from app.utils.avatar import avatar_color_for
from app.utils.ids import new_id


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_phone(self, phone_number: str) -> User | None:
        return await self._session.scalar(select(User).where(User.phone_number == phone_number))

    async def get_by_username(self, username: str) -> User | None:
        return await self._session.scalar(select(User).where(User.username == username))

    async def create(self, *, phone_number: str, display_name: str) -> User:
        user_id = new_id()
        user = User(
            id=user_id,
            phone_number=phone_number,
            display_name=display_name,
            avatar_color=avatar_color_for(user_id),
        )
        self.add(user)
        await self.flush()
        return user
