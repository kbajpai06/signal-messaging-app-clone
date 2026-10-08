from sqlalchemy.exc import IntegrityError

from app.core.errors import AppError, ConflictError, NotFoundError
from app.core.uow import UnitOfWork
from app.models.user import User
from app.repositories.contact_repo import ContactRepository
from app.repositories.user_repo import UserRepository
from app.schemas.contact import ContactCreate, ContactOut
from app.services.events import EventPublisher
from app.services.presenters import contact_out


class ContactService:
    def __init__(
        self,
        *,
        contacts: ContactRepository,
        users: UserRepository,
        events: EventPublisher,
        uow: UnitOfWork,
    ) -> None:
        self._contacts = contacts
        self._users = users
        self._events = events
        self._uow = uow

    async def list_for(self, user: User) -> list[ContactOut]:
        rows = await self._contacts.list_with_users(user.id)
        return [contact_out(c, u, is_online=self._events.is_online) for c, u in rows]

    async def add(self, user: User, data: ContactCreate) -> ContactOut:
        if data.user_id is not None:
            target = await self._users.get(data.user_id)
        else:
            target = await self._users.get_by_phone(data.phone_number or "")
        if target is None:
            raise NotFoundError("No Signal user found with those details", code="user_not_found")
        if target.id == user.id:
            raise AppError("You cannot add yourself as a contact", code="invalid_target")
        if await self._contacts.find(user.id, target.id) is not None:
            raise ConflictError("Already in your contacts", code="contact_exists")

        try:
            contact = await self._contacts.create(
                owner_id=user.id, contact_user_id=target.id, nickname=data.nickname
            )
            await self._uow.commit()
        except IntegrityError as exc:
            await self._uow.rollback()
            raise ConflictError("Already in your contacts", code="contact_exists") from exc
        return contact_out(contact, target, is_online=self._events.is_online)

    async def remove(self, user: User, contact_id: str) -> None:
        contact = await self._contacts.get_for_owner(user.id, contact_id)
        if contact is None:
            raise NotFoundError("Contact not found", code="contact_not_found")
        await self._contacts.delete(contact)
        await self._uow.commit()
