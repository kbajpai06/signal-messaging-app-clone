from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.models.user import User
from app.realtime.gateway import RealtimeGateway
from app.repositories.contact_repo import ContactRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.user_repo import UserRepository
from app.services import factory
from app.services.auth_service import AuthContext, AuthService
from app.services.avatar_service import AvatarService
from app.services.contact_service import ContactService
from app.services.conversation_service import ConversationService
from app.services.events import EventPublisher
from app.services.group_service import GroupService
from app.services.message_service import MessageService
from app.services.receipt_service import ReceiptService
from app.services.user_service import UserService

bearer_scheme = HTTPBearer(auto_error=False)


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


SettingsDep = Annotated[Settings, Depends(get_app_settings)]


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request. Services commit explicitly; closing rolls back leftovers."""
    async with request.app.state.session_factory() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


def get_events(request: Request) -> EventPublisher:
    return request.app.state.events


EventsDep = Annotated[EventPublisher, Depends(get_events)]


def get_gateway(request: Request) -> RealtimeGateway:
    return request.app.state.gateway


GatewayDep = Annotated[RealtimeGateway, Depends(get_gateway)]


def get_avatar_service(request: Request, settings: SettingsDep) -> AvatarService:
    return AvatarService(request.app.state.file_storage, max_bytes=settings.max_upload_bytes)


AvatarServiceDep = Annotated[AvatarService, Depends(get_avatar_service)]


# --- service factories (wiring lives in app.services.factory) -----------------------------


def get_auth_service(db: DbSession, settings: SettingsDep) -> AuthService:
    return factory.build_auth_service(db, settings)


def get_user_service(db: DbSession, avatars: AvatarServiceDep) -> UserService:
    return UserService(
        users=UserRepository(db), contacts=ContactRepository(db), avatars=avatars, uow=db
    )


def get_contact_service(db: DbSession, events: EventsDep) -> ContactService:
    return ContactService(
        contacts=ContactRepository(db), users=UserRepository(db), events=events, uow=db
    )


def get_conversation_service(db: DbSession, events: EventsDep) -> ConversationService:
    return ConversationService(
        conversations=ConversationRepository(db),
        members=MemberRepository(db),
        users=UserRepository(db),
        access=factory.build_access(db),
        appender=factory.build_appender(db),
        events=events,
        uow=db,
    )


def get_group_service(db: DbSession, events: EventsDep, avatars: AvatarServiceDep) -> GroupService:
    return GroupService(
        conversations=ConversationRepository(db),
        members=MemberRepository(db),
        users=UserRepository(db),
        access=factory.build_access(db),
        appender=factory.build_appender(db),
        avatars=avatars,
        events=events,
        uow=db,
    )


def get_message_service(db: DbSession, events: EventsDep) -> MessageService:
    return factory.build_message_service(db, events)


def get_receipt_service(db: DbSession, events: EventsDep) -> ReceiptService:
    return factory.build_receipt_service(db, events)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ContactServiceDep = Annotated[ContactService, Depends(get_contact_service)]
ConversationServiceDep = Annotated[ConversationService, Depends(get_conversation_service)]
GroupServiceDep = Annotated[GroupService, Depends(get_group_service)]
MessageServiceDep = Annotated[MessageService, Depends(get_message_service)]
ReceiptServiceDep = Annotated[ReceiptService, Depends(get_receipt_service)]


# --- authentication ----------------------------------------------------------------------


async def get_auth_context(
    auth_service: AuthServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> AuthContext:
    if credentials is None:
        raise UnauthorizedError("Missing bearer token", code="missing_token")
    return await auth_service.authenticate(credentials.credentials)


AuthContextDep = Annotated[AuthContext, Depends(get_auth_context)]


async def get_current_user(context: AuthContextDep) -> User:
    return context.user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
