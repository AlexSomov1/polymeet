"""Фикстуры интеграционных тестов: настоящие PostgreSQL и Redis.

Адреса берутся из ``TEST_DATABASE_URL`` и ``TEST_REDIS_URL``; если переменных нет,
сервисы поднимаются через testcontainers. Публичный интерфейс для тестов
следующих этапов — фикстуры ``client``, ``create_user``, ``create_meeting`` и ``auth_headers``.
"""

import asyncio
import itertools
import os
import sys
from collections.abc import AsyncIterator, Iterator
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from alembic import command
from fastapi import FastAPI
from redis.asyncio import Redis
from sqlalchemy import pool, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.core.config import Settings
from app.core.db import create_engine
from app.core.redis import create_redis
from app.core.security import create_token, hash_password
from app.main import create_app
from app.models.enums import GeoStatus, MeetingStatus
from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.meeting_repository import MeetingRepository
from app.repositories.user_repository import UserRepository
from tests.conftest import make_settings
from tests.integration.helpers import (
    DEFAULT_PASSWORD,
    AuthHeaders,
    CreateMeeting,
    CreateUser,
    alembic_config,
    app_client,
)

# Таблицы, которые не очищаются между тестами: версия схемы и справочник из миграций.
KEPT_TABLES = frozenset({"alembic_version", "categories"})


def _asyncpg_url(url: str) -> str:
    for prefix in ("postgresql://", "postgres://"):
        if url.startswith(prefix):
            return "postgresql+asyncpg://" + url.removeprefix(prefix)
    return url


@pytest.fixture(scope="session")
def service_urls() -> Iterator[tuple[str, str]]:
    database_url = os.environ.get("TEST_DATABASE_URL")
    redis_url = os.environ.get("TEST_REDIS_URL")
    if sys.platform == "darwin":
        # Docker Desktop: контейнер Ryuk монтирует сокет внутри VM, а там он всегда
        # /var/run/docker.sock (путь хоста ~/.docker/run/docker.sock смонтировать нельзя).
        os.environ.setdefault("TESTCONTAINERS_DOCKER_SOCKET_OVERRIDE", "/var/run/docker.sock")
    with ExitStack() as stack:
        if not database_url:
            postgres = stack.enter_context(
                PostgresContainer("postgres:16-alpine", driver="asyncpg")
            )
            database_url = postgres.get_connection_url()
        if not redis_url:
            redis = stack.enter_context(RedisContainer("redis:7-alpine"))
            host, port = redis.get_container_host_ip(), redis.get_exposed_port(6379)
            redis_url = f"redis://{host}:{port}/0"
        yield _asyncpg_url(database_url), redis_url


@pytest.fixture(scope="session")
def settings(service_urls: tuple[str, str]) -> Settings:
    database_url, redis_url = service_urls
    return make_settings(database_url=database_url, redis_url=redis_url)


async def _recreate_public_schema(database_url: str) -> None:
    engine = create_async_engine(database_url, poolclass=pool.NullPool)
    try:
        async with engine.begin() as conn:
            await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            await conn.execute(text("CREATE SCHEMA public"))
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
async def engine(settings: Settings) -> AsyncIterator[AsyncEngine]:
    """Схема public пересоздаётся и мигрируется до head один раз за сессию."""
    await _recreate_public_schema(settings.database_url)
    # env.py Alembic запускает собственный event loop, поэтому — в отдельном потоке.
    await asyncio.to_thread(command.upgrade, alembic_config(settings), "head")
    engine = create_engine(settings.database_url, pool_size=5)
    yield engine
    await engine.dispose()


@pytest.fixture(autouse=True)
async def _truncate_tables(engine: AsyncEngine) -> None:
    async with engine.begin() as conn:
        tables = await conn.scalars(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        names = sorted(set(tables) - KEPT_TABLES)
        if names:
            quoted = ", ".join(f'"{name}"' for name in names)
            await conn.execute(text(f"TRUNCATE {quoted} RESTART IDENTITY CASCADE"))


@pytest.fixture
async def redis(settings: Settings) -> AsyncIterator[Redis]:
    client = create_redis(settings.redis_url)
    await client.flushdb()
    yield client
    await client.aclose()


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
async def client(app: FastAPI, redis: Redis) -> AsyncIterator[httpx.AsyncClient]:
    async with app_client(app) as http_client:
        yield http_client


@pytest.fixture
def create_user(engine: AsyncEngine, settings: Settings) -> CreateUser:
    counter = itertools.count(1)

    async def _create_user(
        email: str | None = None,
        password: str = DEFAULT_PASSWORD,
        display_name: str | None = None,
        role: int = 0,
    ) -> User:
        number = next(counter)
        password_hash = await hash_password(password, settings=settings)
        async with AsyncSession(engine, expire_on_commit=False) as session:
            user = await UserRepository(session).create(
                email=email or f"user{number}@example.com",
                password_hash=password_hash,
                display_name=display_name or f"Пользователь {number}",
                role=role,
            )
            await session.commit()
        return user

    return _create_user


@pytest.fixture
def create_meeting(engine: AsyncEngine) -> CreateMeeting:
    async def _create_meeting(
        organizer: User,
        *,
        status: MeetingStatus = MeetingStatus.PUBLISHED,
        starts_at: datetime | None = None,
        capacity: int = 10,
        accepted_count: int = 0,
        auto_accept: bool = False,
        category_id: int = 1,
        lat: float | None = None,
        lon: float | None = None,
        title: str = "Встреча",
        description: str = "",
    ) -> Meeting:
        meeting = Meeting(
            organizer_id=organizer.id,
            category_id=category_id,
            status=status,
            geo_status=GeoStatus.PENDING if lat is None else GeoStatus.RESOLVED,
            title=title,
            description=description,
            starts_at=starts_at or datetime.now(UTC) + timedelta(days=7),
            duration_minutes=90,
            address="Санкт-Петербург, Политехническая ул., 29",
            lat=lat,
            lon=lon,
            capacity=capacity,
            accepted_count=accepted_count,
            auto_accept=auto_accept,
        )
        async with AsyncSession(engine, expire_on_commit=False) as session:
            await MeetingRepository(session).add(meeting)
            await session.commit()
        return meeting

    return _create_meeting


@pytest.fixture
def auth_headers(settings: Settings) -> AuthHeaders:
    def _auth_headers(user: User, ttl: timedelta | None = None) -> dict[str, str]:
        token = create_token(str(user.id), "access", ttl, settings=settings)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers
