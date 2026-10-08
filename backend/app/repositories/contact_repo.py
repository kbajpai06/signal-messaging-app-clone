from collections.abc import Collection

from sqlalchemy import func, select

from app.models.contact import Contact
from app.models.user import User
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    model = Contact

    async def get_for_owner(self, owner_id: str, contact_id: str) -> Contact | None:
        result = await self._session.execute(
            select(Contact).where(Contact.id == contact_id, Contact.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def find(self, owner_id: str, contact_user_id: str) -> Contact | None:
        result = await self._session.execute(
            select(Contact).where(
                Contact.owner_id == owner_id, Contact.contact_user_id == contact_user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_with_users(self, owner_id: str) -> list[tuple[Contact, User]]:
        stmt = (
            select(Contact, User)
            .join(User, User.id == Contact.contact_user_id)
            .where(Contact.owner_id == owner_id)
            .order_by(func.lower(func.coalesce(Contact.nickname, User.display_name)), Contact.id)
        )
        return [(contact, user) for contact, user in (await self._session.execute(stmt)).all()]

    async def contact_user_ids_among(self, owner_id: str, user_ids: Collection[str]) -> set[str]:
        if not user_ids:
            return set()
        stmt = select(Contact.contact_user_id).where(
            Contact.owner_id == owner_id, Contact.contact_user_id.in_(user_ids)
        )
        return set((await self._session.scalars(stmt)).all())

    async def create(self, *, owner_id: str, contact_user_id: str, nickname: str | None) -> Contact:
        contact = Contact(owner_id=owner_id, contact_user_id=contact_user_id, nickname=nickname)
        self.add(contact)
        await self.flush()
        return contact
