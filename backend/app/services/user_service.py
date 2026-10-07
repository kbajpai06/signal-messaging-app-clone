from collections.abc import Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError
from app.core.uow import UnitOfWork
from app.models.user import User
from app.repositories.user_repo import UserRepository

EDITABLE_FIELDS = frozenset({"display_name", "about", "username"})


class UserService:
    def __init__(self, *, users: UserRepository, uow: UnitOfWork) -> None:
        self._users = users
        self._uow = uow

    async def update_profile(self, user: User, changes: Mapping[str, Any]) -> User:
        updates = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS}

        username = updates.get("username")
        if username is not None:
            existing = await self._users.get_by_username(username)
            if existing is not None and existing.id != user.id:
                raise ConflictError("That username is already taken", code="username_taken")

        for field, value in updates.items():
            setattr(user, field, value)

        try:
            await self._uow.commit()
        except IntegrityError as exc:
            await self._uow.rollback()
            raise ConflictError("That username is already taken", code="username_taken") from exc
        return user
