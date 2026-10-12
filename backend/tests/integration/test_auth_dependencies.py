from datetime import timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings
from app.core.security import create_token
from app.models.user import User
from tests.conftest import make_settings
from tests.integration.helpers import AuthHeaders, CreateUser, add_probe_routes


@pytest.fixture
def app(app: FastAPI) -> FastAPI:
    add_probe_routes(app)
    return app


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_valid_access_token_resolves_current_user(
    client: httpx.AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    user = await create_user()

    response = await client.get("/_probe/me", headers=auth_headers(user))

    assert response.status_code == 200
    assert response.json() == {"id": user.id}


async def _delete_user(engine: AsyncEngine, user: User) -> None:
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM users WHERE id = :id"), {"id": user.id})


@pytest.mark.parametrize(
    "case",
    [
        "no_token",
        "not_bearer",
        "expired",
        "forged",
        "refresh_token",
        "non_numeric_subject",
        "deleted_user",
    ],
)
async def test_current_user_rejects_invalid_credentials(
    client: httpx.AsyncClient,
    engine: AsyncEngine,
    settings: Settings,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    case: str,
) -> None:
    user = await create_user()
    forger = make_settings(jwt_secret="attacker-secret-of-sufficient-length")
    headers = {
        "no_token": {},
        "not_bearer": {"Authorization": "Basic dXNlcjpwYXNz"},
        "expired": auth_headers(user, ttl=timedelta(seconds=-1)),
        "forged": _bearer(create_token(str(user.id), "access", settings=forger)),
        "refresh_token": _bearer(create_token(str(user.id), "refresh", settings=settings)),
        "non_numeric_subject": _bearer(create_token("not-a-number", "access", settings=settings)),
        "deleted_user": auth_headers(user),
    }[case]
    if case == "deleted_user":
        await _delete_user(engine, user)

    response = await client.get("/_probe/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHORIZED"
    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_optional_user_is_anonymous_only_without_token(
    client: httpx.AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    user = await create_user()

    anonymous = await client.get("/_probe/maybe-me")
    authorized = await client.get("/_probe/maybe-me", headers=auth_headers(user))
    expired = await client.get(
        "/_probe/maybe-me", headers=auth_headers(user, ttl=timedelta(seconds=-1))
    )

    assert anonymous.json() == {"id": None}
    assert authorized.json() == {"id": user.id}
    # Просроченный токен — повод обновить его, а не молча стать анонимом.
    assert expired.status_code == 401
