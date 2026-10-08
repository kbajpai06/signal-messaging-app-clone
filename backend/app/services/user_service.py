from collections.abc import Mapping
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.core.errors import ConflictError
from app.core.uow import UnitOfWork
from app.models.user import User
from app.repositories.contact_repo import ContactRepository
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserDirectoryEntry
from app.services.avatar_service import AvatarService
from app.services.presenters import directory_entry

EDITABLE_FIELDS = frozenset({"display_name", "about", "username"})
SEARCH_LIMIT = 20


class UserService:
    def __init__(
        self,
        *,
        users: UserRepository,
        contacts: ContactRepository,
        avatars: AvatarService,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._contacts = contacts
        self._avatars = avatars
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

    async def search(self, user: User, query: str) -> list[UserDirectoryEntry]:
        found = await self._users.search(query, exclude_id=user.id, limit=SEARCH_LIMIT)
        contact_ids = await self._contacts.contact_user_ids_among(user.id, [u.id for u in found])
        return [directory_entry(u, is_contact=u.id in contact_ids) for u in found]

    async def set_avatar(self, user: User, data: bytes) -> User:
        new_url = await self._avatars.store(data)
        previous_url = user.avatar_url
        user.avatar_url = new_url
        try:
            await self._uow.commit()
        except Exception:
            await self._uow.rollback()
            await self._avatars.discard(new_url)
            raise
        await self._avatars.discard(previous_url)
        return user
