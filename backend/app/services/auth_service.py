import hmac
import logging
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.core.security import decode_token, encode_token
from app.core.uow import UnitOfWork
from app.models.user import User
from app.repositories.session_repo import UserSessionRepository
from app.repositories.user_repo import UserRepository
from app.utils.time import now_ms

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthResult:
    token: str
    expires_at: int
    user: User
    is_new_user: bool


@dataclass(frozen=True)
class AuthContext:
    user: User
    session_id: str


class AuthService:
    def __init__(
        self,
        *,
        users: UserRepository,
        sessions: UserSessionRepository,
        uow: UnitOfWork,
        settings: Settings,
    ) -> None:
        self._users = users
        self._sessions = sessions
        self._uow = uow
        self._settings = settings

    async def request_otp(self, phone_number: str) -> None:
        """Mocked: nothing is sent. The OTP is the fixed OTP_FIXED_CODE."""
        logger.info("Mock OTP requested for %s", phone_number)

    async def verify_otp(
        self, *, phone_number: str, code: str, device_label: str | None
    ) -> AuthResult:
        if not hmac.compare_digest(code.encode(), self._settings.otp_fixed_code.encode()):
            raise UnauthorizedError("Incorrect verification code", code="invalid_otp")

        user, is_new_user = await self._get_or_create_user(phone_number)

        created_at = now_ms()
        expires_at = created_at + self._settings.access_token_ttl_min * 60_000
        user_session = await self._sessions.create(
            user_id=user.id,
            device_label=device_label,
            created_at=created_at,
            expires_at=expires_at,
        )
        await self._uow.commit()

        token = encode_token(
            user_id=user.id,
            session_id=user_session.id,
            expires_at_ms=expires_at,
            secret_key=self._settings.secret_key,
        )
        return AuthResult(token=token, expires_at=expires_at, user=user, is_new_user=is_new_user)

    async def authenticate(self, token: str) -> AuthContext:
        """Validate a bearer token against its session row. Reused by the WS handshake."""
        claims = decode_token(token, self._settings.secret_key)

        user_session = await self._sessions.get(claims.session_id)
        if (
            user_session is None
            or user_session.user_id != claims.user_id
            or user_session.revoked_at is not None
            or user_session.expires_at <= now_ms()
        ):
            raise UnauthorizedError("Session is no longer valid", code="session_invalid")

        user = await self._users.get(claims.user_id)
        if user is None:
            raise UnauthorizedError("Session is no longer valid", code="session_invalid")
        return AuthContext(user=user, session_id=user_session.id)

    async def logout(self, session_id: str) -> None:
        await self._sessions.revoke(session_id, now_ms())
        await self._uow.commit()

    async def _get_or_create_user(self, phone_number: str) -> tuple[User, bool]:
        user = await self._users.get_by_phone(phone_number)
        if user is not None:
            return user, False
        try:
            # New users start with their phone number as display name; onboarding replaces it.
            user = await self._users.create(phone_number=phone_number, display_name=phone_number)
        except IntegrityError:
            # Lost a race with a concurrent registration for the same number.
            await self._uow.rollback()
            existing = await self._users.get_by_phone(phone_number)
            if existing is None:
                raise
            return existing, False
        return user, True
