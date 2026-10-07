from sqlalchemy import update

from app.models.session import UserSession
from app.repositories.base import BaseRepository


class UserSessionRepository(BaseRepository[UserSession]):
    model = UserSession

    async def create(
        self, *, user_id: str, device_label: str | None, created_at: int, expires_at: int
    ) -> UserSession:
        user_session = UserSession(
            user_id=user_id,
            device_label=device_label,
            created_at=created_at,
            expires_at=expires_at,
        )
        self.add(user_session)
        await self.flush()
        return user_session

    async def revoke(self, session_id: str, at_ms: int) -> None:
        await self._session.execute(
            update(UserSession)
            .where(UserSession.id == session_id, UserSession.revoked_at.is_(None))
            .values(revoked_at=at_ms)
        )
