from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.errors import UnauthorizedError
from app.models.user import User
from app.repositories.session_repo import UserSessionRepository
from app.repositories.user_repo import UserRepository
from app.services.auth_service import AuthContext, AuthService
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


def get_auth_service(db: DbSession, settings: SettingsDep) -> AuthService:
    return AuthService(
        users=UserRepository(db),
        sessions=UserSessionRepository(db),
        uow=db,
        settings=settings,
    )


def get_user_service(db: DbSession) -> UserService:
    return UserService(users=UserRepository(db), uow=db)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]


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
