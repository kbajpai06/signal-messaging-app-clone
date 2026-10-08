"""Service wiring shared by the REST dependencies and the WebSocket handlers."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.message_repo import MessageRepository
from app.repositories.presence_repo import PresenceRepository
from app.repositories.session_repo import UserSessionRepository
from app.repositories.user_repo import UserRepository
from app.services.access import ConversationAccess
from app.services.auth_service import AuthService
from app.services.events import EventPublisher
from app.services.message_appender import MessageAppender
from app.services.message_service import MessageService
from app.services.presence_service import PresenceService
from app.services.receipt_service import ReceiptService
from app.services.sync_service import SyncService
from app.services.typing_service import TypingService


def build_access(db: AsyncSession) -> ConversationAccess:
    return ConversationAccess(
        conversations=ConversationRepository(db), members=MemberRepository(db)
    )


def build_appender(db: AsyncSession) -> MessageAppender:
    return MessageAppender(
        conversations=ConversationRepository(db),
        members=MemberRepository(db),
        messages=MessageRepository(db),
    )


def build_auth_service(db: AsyncSession, settings: Settings) -> AuthService:
    return AuthService(
        users=UserRepository(db),
        sessions=UserSessionRepository(db),
        uow=db,
        settings=settings,
    )


def build_message_service(db: AsyncSession, events: EventPublisher) -> MessageService:
    return MessageService(
        messages=MessageRepository(db),
        members=MemberRepository(db),
        access=build_access(db),
        appender=build_appender(db),
        events=events,
        uow=db,
    )


def build_receipt_service(db: AsyncSession, events: EventPublisher) -> ReceiptService:
    return ReceiptService(
        members=MemberRepository(db), access=build_access(db), events=events, uow=db
    )


def build_presence_service(db: AsyncSession, events: EventPublisher) -> PresenceService:
    return PresenceService(presence=PresenceRepository(db), events=events, uow=db)


def build_typing_service(db: AsyncSession, events: EventPublisher) -> TypingService:
    return TypingService(access=build_access(db), members=MemberRepository(db), events=events)


def build_sync_service(db: AsyncSession) -> SyncService:
    return SyncService(messages=MessageRepository(db), members=MemberRepository(db))
