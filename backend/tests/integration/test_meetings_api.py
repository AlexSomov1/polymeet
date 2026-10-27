from datetime import UTC, datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.api.deps import get_geocoding
from app.models.enums import GeoStatus
from app.models.meeting import Meeting
from app.models.user import User
from tests.integration.helpers import AuthHeaders, CreateUser


def meeting_data(**changes: object) -> dict[str, object]:
    data: dict[str, object] = {
        "title": "  Вечер игр  ",
        "description": "Настолки",
        "category": "games",
        "starts_at": (datetime.now(UTC) + timedelta(days=30)).isoformat(),
        "duration_minutes": 120,
        "address": "  Санкт-Петербург, Литейный 12  ",
        "capacity": 6,
    }
    data.update(changes)
    return data


async def create_meeting(
    client: httpx.AsyncClient, user: User, auth_headers: AuthHeaders, **changes: object
) -> httpx.Response:
    return await client.post(
        "/api/v1/meetings", json=meeting_data(**changes), headers=auth_headers(user)
    )


async def test_categories_are_seeded_in_order(client: httpx.AsyncClient) -> None:
    response = await client.get("/api/v1/categories")
    assert response.status_code == 200
    assert [(item["id"], item["slug"]) for item in response.json()] == [
        (1, "lecture"),
        (2, "games"),
        (3, "concert"),
        (4, "sport"),
        (5, "walk"),
        (6, "other"),
    ]


async def test_create_visibility_and_lifecycle(
    client: httpx.AsyncClient, create_user: CreateUser, auth_headers: AuthHeaders
) -> None:
    owner, stranger = await create_user(), await create_user()
    response = await create_meeting(client, owner, auth_headers)
    assert response.status_code == 201, response.text
    meeting = response.json()
    assert (meeting["title"], meeting["address"]) == ("Вечер игр", "Санкт-Петербург, Литейный 12")
    assert (meeting["status"], meeting["geo_status"], meeting["free_places"]) == (
        "draft",
        "pending",
        6,
    )
    assert meeting["lat"] is None and meeting["my_application"] is None
    path = f"/api/v1/meetings/{meeting['id']}"
    assert (await client.get(path, headers=auth_headers(owner))).status_code == 200
    assert (await client.get(path, headers=auth_headers(stranger))).status_code == 404
    assert (await client.get(path)).status_code == 404
    assert (
        await client.patch(path, json={"title": "Чужая встреча"}, headers=auth_headers(stranger))
    ).status_code == 404

    updated = await client.patch(
        path, json={"title": "Вечер настолок", "status": "published"}, headers=auth_headers(owner)
    )
    assert updated.status_code == 200, updated.text
    assert (updated.json()["title"], updated.json()["status"]) == ("Вечер настолок", "published")
    assert (await client.get(path)).status_code == 200
    assert (
        await client.patch(path, json={"title": "Нет"}, headers=auth_headers(stranger))
    ).status_code == 403
    cancelled = await client.patch(path, json={"status": "cancelled"}, headers=auth_headers(owner))
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    blocked = await client.patch(path, json={"title": "После отмены"}, headers=auth_headers(owner))
    assert (blocked.status_code, blocked.json()["code"]) == (409, "INVALID_TRANSITION")


@pytest.mark.parametrize(
    "changes,field",
    [
        ({"starts_at": "2020-01-01T00:00:00Z"}, "starts_at"),
        ({"category": "unknown"}, "category"),
        ({"title": "  Я  "}, "title"),
        ({"address": "  Я  "}, "address"),
    ],
)
async def test_create_rejects_invalid_domain_values(
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    changes: dict[str, object],
    field: str,
) -> None:
    response = await create_meeting(client, await create_user(), auth_headers, **changes)
    assert response.status_code == 400
    assert field in {item["field"] for item in response.json()["errors"]}


async def test_patch_uses_final_start_time_and_guards_capacity(
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    engine: AsyncEngine,
) -> None:
    owner = await create_user()
    created = await create_meeting(client, owner, auth_headers)
    meeting_id = created.json()["id"]
    path = f"/api/v1/meetings/{meeting_id}"
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE meetings SET starts_at = now() - interval '1 day', "
                "accepted_count = 3 WHERE id = :id"
            ),
            {"id": meeting_id},
        )
    past = await client.patch(path, json={"status": "published"}, headers=auth_headers(owner))
    assert past.status_code == 400
    assert past.json()["errors"][0]["field"] == "starts_at"
    too_small = await client.patch(path, json={"capacity": 2}, headers=auth_headers(owner))
    assert too_small.status_code == 400
    assert too_small.json()["errors"][0]["field"] == "capacity"
    fixed = await client.patch(
        path,
        json={
            "starts_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
            "capacity": 3,
            "status": "published",
        },
        headers=auth_headers(owner),
    )
    assert fixed.status_code == 200, fixed.text
    assert (fixed.json()["status"], fixed.json()["free_places"]) == ("published", 0)


async def test_my_meetings_keyset_pagination_and_cursor_errors(
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    engine: AsyncEngine,
) -> None:
    owner, stranger = await create_user(), await create_user()
    ids = []
    for number in range(7):
        response = await create_meeting(client, owner, auth_headers, title=f"Встреча {number}")
        assert response.status_code == 201
        ids.append(response.json()["id"])
    await create_meeting(client, stranger, auth_headers)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "UPDATE meetings SET created_at = '2030-01-01T00:00:00Z' WHERE organizer_id = :id"
            ),
            {"id": owner.id},
        )
    collected: list[int] = []
    cursor = None
    while True:
        response = await client.get(
            "/api/v1/users/me/meetings",
            params={"limit": 3, **({"cursor": cursor} if cursor else {})},
            headers=auth_headers(owner),
        )
        assert response.status_code == 200, response.text
        page = response.json()
        collected.extend(item["id"] for item in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert collected == sorted(ids, reverse=True)
    bad = await client.get(
        "/api/v1/users/me/meetings", params={"cursor": "not-a-cursor"}, headers=auth_headers(owner)
    )
    assert bad.status_code == 400
    assert bad.json()["errors"][0]["field"] == "cursor"


@pytest.mark.parametrize("cached", [False, True])
async def test_port_is_called_before_and_after_commit(
    app: FastAPI,
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    engine: AsyncEngine,
    cached: bool,
) -> None:
    events: list[str] = []

    class Port:
        async def resolve_cached(self, meeting: Meeting) -> bool:
            events.append("resolve")
            async with AsyncSession(engine) as session:
                assert await session.get(Meeting, meeting.id) is None
            if cached:
                meeting.lat = 59.9
                meeting.lon = 30.3
                meeting.geo_status = GeoStatus.RESOLVED
            return cached

        async def enqueue(self, meeting_id: int) -> None:
            events.append("enqueue")
            async with AsyncSession(engine) as session:
                assert (
                    await session.scalar(select(Meeting).where(Meeting.id == meeting_id))
                    is not None
                )

    port = Port()
    app.dependency_overrides[get_geocoding] = lambda: port
    try:
        created = await create_meeting(client, await create_user(), auth_headers)
        assert created.status_code == 201, created.text
        assert created.json()["geo_status"] == ("resolved" if cached else "pending")
        assert events == (["resolve"] if cached else ["resolve", "enqueue"])
    finally:
        app.dependency_overrides.clear()


async def test_address_change_clears_coordinates_and_updates_timestamp(
    app: FastAPI,
    client: httpx.AsyncClient,
    create_user: CreateUser,
    auth_headers: AuthHeaders,
    engine: AsyncEngine,
) -> None:
    calls: list[str] = []

    class Port:
        async def resolve_cached(self, meeting: Meeting) -> bool:
            calls.append("resolve")
            if len(calls) == 1:
                meeting.lat, meeting.lon = 59.9, 30.3
                meeting.address_norm = "Старый адрес"
                meeting.geo_status = GeoStatus.RESOLVED
                return True
            return False

        async def enqueue(self, meeting_id: int) -> None:
            calls.append("enqueue")

    app.dependency_overrides[get_geocoding] = lambda: Port()
    try:
        owner = await create_user()
        created = await create_meeting(client, owner, auth_headers)
        assert created.status_code == 201, created.text
        meeting_id = created.json()["id"]
        async with AsyncSession(engine) as session:
            original = await session.get(Meeting, meeting_id)
            assert original is not None
            previous_updated_at = original.updated_at
        path = f"/api/v1/meetings/{meeting_id}"
        same = await client.patch(
            path,
            json={"address": "  Санкт-Петербург, Литейный 12  "},
            headers=auth_headers(owner),
        )
        assert same.status_code == 200
        assert (same.json()["lat"], calls) == (59.9, ["resolve"])
        changed = await client.patch(
            path, json={"address": "Невский проспект 1"}, headers=auth_headers(owner)
        )
        assert changed.status_code == 200, changed.text
        assert changed.json()["geo_status"] == "pending"
        assert changed.json()["lat"] is None and changed.json()["lon"] is None
        assert changed.json()["address_norm"] is None
        assert calls == ["resolve", "resolve", "enqueue"]
        async with AsyncSession(engine) as session:
            current = await session.get(Meeting, meeting_id)
            assert current is not None
            assert current.updated_at > previous_updated_at
    finally:
        app.dependency_overrides.clear()
