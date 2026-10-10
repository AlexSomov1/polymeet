from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.db import get_session
from app.core.errors import UnauthorizedError
from app.core.logging import bind_request_context
from app.core.security import INVALID_TOKEN_MESSAGE, decode_token
from app.models.user import User
from app.repositories.user_repository import UserRepository

_bearer = HTTPBearer(auto_error=False, description="Access-токен, выданный /auth/login")


async def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]
_CredentialsDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


async def get_current_user_optional(
    credentials: _CredentialsDep,
    session: SessionDep,
    settings: SettingsDep,
) -> User | None:
    """Пользователь по Bearer-токену или ``None`` без токена.

    Переданный, но недействительный токен — это 401, а не анонимный доступ:
    клиент должен обновить токен.
    """
    if credentials is None:
        return None
    claims = decode_token(credentials.credentials, "access", settings=settings)
    user = await UserRepository(session).get_by_id(claims.sub)
    if user is None:
        raise UnauthorizedError(INVALID_TOKEN_MESSAGE)
    bind_request_context(user_id=user.id)
    return user


async def get_current_user(
    user: Annotated[User | None, Depends(get_current_user_optional)],
) -> User:
    if user is None:
        raise UnauthorizedError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
