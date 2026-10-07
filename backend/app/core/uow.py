from typing import Protocol


class UnitOfWork(Protocol):
    """Transaction boundary owned by services. SQLAlchemy's AsyncSession satisfies it."""

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
