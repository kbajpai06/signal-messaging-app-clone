from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


class BaseRepository[T: Base]:
    """Repositories are the only layer that talks to the ORM/SQL."""

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, entity_id: str) -> T | None:
        return await self._session.get(self.model, entity_id)

    def add(self, entity: T) -> T:
        self._session.add(entity)
        return entity

    async def flush(self) -> None:
        await self._session.flush()

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
