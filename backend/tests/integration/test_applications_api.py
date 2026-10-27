from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.enums import ApplicationStatus, MeetingStatus
from app.models.meeting import Meeting
from app.models.user import User
from tests.integration.helpers import AuthHeaders, CreateMeeting, CreateUser


async def assert_invariant(engine: AsyncEngine, meeting_id: int) -> None:
    """``accepted_count`` равен числу принятых заявок и не больше ``capacity``."""
    async with engine.connect() as conn:
        row = (
            await conn.execute(
                text(
                    "SELECT m.accepted_count, m.capacity, "
                    "(SELECT count(*) FROM applications a "
                    " WHERE a.meeting_id = m.id AND a.status = 1) "
                    "FROM meetings m WHERE m.id = :id"
                ),
                {"id": meeting_id},
            )
        ).one()
    accepted_count, capacity, accepted = row
    assert accepted_count == accepted <= capacity


async def statuses_by_user(engine: AsyncEngine, meeting: Meeting) -> dict[int, str]:
    async with engine.connect() as conn:
        rows = await conn.execute(
            text("SELECT user_id, status FROM applications WHERE meeting_id = :id"),
            {"id": meeting.id},
        )
        return {user_id: ApplicationStatus(status).name.lower() for user_id, status in rows}


def applications_url(meeting: Meeting) -> str:
    return f"/api/v1/meetings/{meeting.id}/applications"


def decision_url(application_id: int) -> str:
    return f"/api/v1/applications/{application_id}/decision"


class Api:
    """Короткие вызовы API заявок от имени пользователя."""

    def __init__(self, client: httpx.AsyncClient, auth_headers: AuthHeaders) -> None:
        self.client = client
        self.auth_headers = auth_headers

    async def apply(self, user: User, meeting: Meeting, **body: Any) -> httpx.Response:
        return await self.client.post(
            applications_url(meeting), json=body or None, headers=self.auth_headers(user)
        )

    async def applied(self, user: User, meeting: Meeting, **body: Any) -> dict[str, Any]:
        response = await self.apply(user, meeting, **body)
        assert response.status_code == 201, response.text
        result: dict[str, Any] = response.json()
        return result

    async def withdraw(self, user: User, meeting: Meeting) -> httpx.Response:
        return await self.client.delete(
            f"{applications_url(meeting)}/me", headers=self.auth_headers(user)
        )

    async def decide(self, user: User, application_id: int, decision: str) -> httpx.Response:
        return await self.client.post(
            decision_url(application_id),
            json={"decision": decision},
            headers=self.auth_headers(user),
        )


@pytest.fixture
def api(client: httpx.AsyncClient, auth_headers: AuthHeaders) -> Api:
    return Api(client, auth_headers)


@pytest.fixture
async def organizer(create_user: CreateUser) -> User:
    return await create_user()


async def test_auto_accept_and_manual_review(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    auto = await create_meeting(organizer, auto_accept=True)
    manual = await create_meeting(organizer)
    user = await create_user()

    accepted = await api.applied(user, auto, message="  Возьму шахматы  ")
    assert (accepted["status"], accepted["message"]) == ("accepted", "Возьму шахматы")
    assert accepted["decided_at"] is not None
    assert accepted["user"] == {
        "id": user.id,
        "display_name": user.display_name,
        "attendance_rate": None,
        "attended_count": 0,
    }
    card = await api.client.get(f"/api/v1/meetings/{auto.id}")
    assert card.json()["accepted_count"] == 1

    pending = await api.applied(user, manual, message="   ")
    assert (pending["status"], pending["message"], pending["decided_at"]) == (
        "pending",
        None,
        None,
    )
    # Тело запроса необязательно
    no_body = await api.client.post(
        applications_url(manual), headers=api.auth_headers(await create_user())
    )
    assert no_body.status_code == 201
    for meeting in (auto, manual):
        await assert_invariant(engine, meeting.id)


async def test_full_meeting_puts_new_applications_on_waitlist(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2, auto_accept=True)
    for _ in range(2):
        assert (await api.applied(await create_user(), meeting))["status"] == "accepted"

    assert (await api.applied(await create_user(), meeting))["status"] == "waitlist"
    await assert_invariant(engine, meeting.id)


async def test_organizer_cannot_accept_over_capacity(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2)
    first, second, third = [await api.applied(await create_user(), meeting) for _ in range(3)]
    for application in (first, second):
        accepted = await api.decide(organizer, application["id"], "accepted")
        assert (accepted.status_code, accepted.json()["status"]) == (200, "accepted")

    response = await api.decide(organizer, third["id"], "accepted")

    assert (response.status_code, response.json()["code"]) == (409, "CAPACITY_REACHED")
    await assert_invariant(engine, meeting.id)


async def test_withdrawing_accepted_promotes_earliest_waitlisted(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2, auto_accept=True)
    accepted, other, early, late = [await create_user() for _ in range(4)]
    for user in (accepted, other, early, late):
        await api.applied(user, meeting)

    response = await api.withdraw(accepted, meeting)

    assert response.status_code == 204
    assert await statuses_by_user(engine, meeting) == {
        accepted.id: "withdrawn",
        other.id: "accepted",
        early.id: "accepted",
        late.id: "waitlist",
    }
    await assert_invariant(engine, meeting.id)


async def test_rejecting_accepted_promotes_next_waitlisted(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2, auto_accept=True)
    accepted, other, waiting = [await create_user() for _ in range(3)]
    application = await api.applied(accepted, meeting)
    await api.applied(other, meeting)
    await api.applied(waiting, meeting)

    response = await api.decide(organizer, application["id"], "rejected")

    assert (response.status_code, response.json()["status"]) == (200, "rejected")
    assert await statuses_by_user(engine, meeting) == {
        accepted.id: "rejected",
        other.id: "accepted",
        waiting.id: "accepted",
    }
    await assert_invariant(engine, meeting.id)


async def test_repeat_application_and_reapply_after_withdrawal(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer)
    user = await create_user()
    first = await api.applied(user, meeting)

    repeated = await api.apply(user, meeting)
    assert (repeated.status_code, repeated.json()["code"]) == (409, "ALREADY_APPLIED")

    assert (await api.withdraw(user, meeting)).status_code == 204
    second = await api.applied(user, meeting)
    assert second["id"] != first["id"]
    await assert_invariant(engine, meeting.id)


@pytest.mark.parametrize(
    ("status", "starts_in", "own", "expected"),
    [
        (MeetingStatus.PUBLISHED, timedelta(days=1), True, (403, "FORBIDDEN")),
        (MeetingStatus.DRAFT, timedelta(days=1), False, (404, "NOT_FOUND")),
        (MeetingStatus.CANCELLED, timedelta(days=1), False, (422, "MEETING_NOT_PUBLISHED")),
        (MeetingStatus.PUBLISHED, -timedelta(minutes=5), False, (422, "MEETING_NOT_PUBLISHED")),
    ],
)
async def test_cannot_apply(
    api: Api,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
    status: MeetingStatus,
    starts_in: timedelta,
    own: bool,
    expected: tuple[int, str],
) -> None:
    meeting = await create_meeting(
        organizer, status=status, starts_at=datetime.now(UTC) + starts_in
    )
    user = organizer if own else await create_user()

    response = await api.apply(user, meeting)

    assert (response.status_code, response.json()["code"]) == expected


async def test_apply_to_missing_meeting_is_not_found(api: Api, create_user: CreateUser) -> None:
    response = await api.client.post(
        "/api/v1/meetings/999999/applications", headers=api.auth_headers(await create_user())
    )
    assert response.status_code == 404


async def test_withdraw_without_application_is_not_found(
    api: Api, organizer: User, create_user: CreateUser, create_meeting: CreateMeeting
) -> None:
    meeting = await create_meeting(organizer)

    missing = await api.withdraw(await create_user(), meeting)

    assert (missing.status_code, missing.json()["code"]) == (404, "NOT_FOUND")


async def test_decision_rules(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer)
    applicant, stranger = await create_user(), await create_user()
    application = await api.applied(applicant, meeting)

    for actor in (applicant, stranger):
        response = await api.decide(actor, application["id"], "accepted")
        assert (response.status_code, response.json()["code"]) == (403, "FORBIDDEN")
    missing = await api.decide(organizer, 999999, "accepted")
    assert missing.status_code == 404

    cancelled = await api.client.patch(
        f"/api/v1/meetings/{meeting.id}",
        json={"status": "cancelled"},
        headers=api.auth_headers(organizer),
    )
    assert cancelled.status_code == 200
    response = await api.decide(organizer, application["id"], "accepted")
    assert (response.status_code, response.json()["code"]) == (409, "INVALID_TRANSITION")
    await assert_invariant(engine, meeting.id)


async def test_organizer_queue(
    api: Api,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2, auto_accept=True)
    users = [await create_user() for _ in range(5)]
    ids = [(await api.applied(user, meeting))["id"] for user in users]

    foreign = await api.client.get(applications_url(meeting), headers=api.auth_headers(users[0]))
    assert (foreign.status_code, foreign.json()["code"]) == (403, "FORBIDDEN")

    seen: list[int] = []
    cursor = None
    while True:
        params: dict[str, Any] = {"limit": 2}
        if cursor is not None:
            params["cursor"] = cursor
        response = await api.client.get(
            applications_url(meeting), params=params, headers=api.auth_headers(organizer)
        )
        assert response.status_code == 200, response.text
        seen += [item["id"] for item in response.json()["items"]]
        cursor = response.json()["next_cursor"]
        if cursor is None:
            break
    assert seen == ids

    waitlist = await api.client.get(
        applications_url(meeting),
        params={"status": "waitlist"},
        headers=api.auth_headers(organizer),
    )
    assert [item["id"] for item in waitlist.json()["items"]] == ids[2:]

    broken = await api.client.get(
        applications_url(meeting), params={"cursor": "broken"}, headers=api.auth_headers(organizer)
    )
    assert (broken.status_code, broken.json()["errors"][0]["field"]) == (400, "cursor")


async def test_my_applications(
    api: Api,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    user = await create_user()
    first = await create_meeting(organizer, title="Шахматы", capacity=2, auto_accept=True)
    second = await create_meeting(organizer, title="Бег")
    accepted = await api.applied(user, first)
    pending = await api.applied(user, second)

    response = await api.client.get("/api/v1/users/me/applications", headers=api.auth_headers(user))
    assert response.status_code == 200
    items = response.json()["items"]
    assert [item["id"] for item in items] == [pending["id"], accepted["id"]]
    assert items[1]["meeting"] == {
        "id": first.id,
        "title": "Шахматы",
        "starts_at": items[1]["meeting"]["starts_at"],
        "status": "published",
        "accepted_count": 1,
        "capacity": 2,
    }

    only_accepted = await api.client.get(
        "/api/v1/users/me/applications",
        params={"status": "accepted"},
        headers=api.auth_headers(user),
    )
    assert [item["id"] for item in only_accepted.json()["items"]] == [accepted["id"]]
    others = await api.client.get(
        "/api/v1/users/me/applications", headers=api.auth_headers(organizer)
    )
    assert others.json() == {"items": [], "next_cursor": None}


async def test_my_application_in_meeting_card(
    api: Api, organizer: User, create_user: CreateUser, create_meeting: CreateMeeting
) -> None:
    meeting = await create_meeting(organizer)
    user = await create_user()
    path = f"/api/v1/meetings/{meeting.id}"

    async def card(viewer: User | None) -> Any:
        headers = api.auth_headers(viewer) if viewer is not None else {}
        return (await api.client.get(path, headers=headers)).json()["my_application"]

    assert await card(None) is None
    assert await card(user) is None
    application = await api.applied(user, meeting)
    assert await card(user) == {"id": application["id"], "status": "pending"}
    assert await card(None) is None
    assert await card(organizer) is None

    await api.withdraw(user, meeting)
    assert await card(user) is None


async def test_capacity_increase_promotes_exactly_new_places(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=2, auto_accept=True)
    users = [await create_user() for _ in range(6)]
    for user in users:
        await api.applied(user, meeting)

    response = await api.client.patch(
        f"/api/v1/meetings/{meeting.id}",
        json={"capacity": 4},
        headers=api.auth_headers(organizer),
    )

    assert response.status_code == 200, response.text
    assert response.json()["accepted_count"] == 4
    statuses = await statuses_by_user(engine, meeting)
    assert [statuses[user.id] for user in users] == ["accepted"] * 4 + ["waitlist"] * 2
    await assert_invariant(engine, meeting.id)


async def test_rejected_applicant_can_neither_reapply_nor_withdraw(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer)
    user = await create_user()
    application = await api.applied(user, meeting)
    assert (await api.decide(organizer, application["id"], "rejected")).status_code == 200

    reapplied = await api.apply(user, meeting)
    assert (reapplied.status_code, reapplied.json()["code"]) == (409, "ALREADY_APPLIED")
    withdrawn = await api.withdraw(user, meeting)
    assert (withdrawn.status_code, withdrawn.json()["code"]) == (409, "INVALID_TRANSITION")
    await assert_invariant(engine, meeting.id)
