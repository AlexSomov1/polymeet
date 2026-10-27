"""Одновременные запросы разных пользователей к одной встрече.

Запросы идут через ``asyncio.gather`` по HTTP; пула приложения (20 соединений плюс 10
сверх лимита) хватает, чтобы все они одновременно ждали блокировку строки встречи.
"""

import asyncio
from collections import Counter

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.user import User
from tests.integration.helpers import AuthHeaders, CreateMeeting, CreateUser
from tests.integration.test_applications_api import Api, assert_invariant, statuses_by_user


@pytest.fixture
def api(client: httpx.AsyncClient, auth_headers: AuthHeaders) -> Api:
    return Api(client, auth_headers)


@pytest.fixture
async def organizer(create_user: CreateUser) -> User:
    return await create_user()


async def test_simultaneous_applications_never_exceed_capacity(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=5, auto_accept=True)
    users = [await create_user() for _ in range(20)]

    responses = await asyncio.gather(*(api.apply(user, meeting) for user in users))

    assert [response.status_code for response in responses] == [201] * 20
    assert Counter(response.json()["status"] for response in responses) == {
        "accepted": 5,
        "waitlist": 15,
    }
    await assert_invariant(engine, meeting.id)


async def test_same_user_applies_once_under_concurrency(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, auto_accept=True)
    user = await create_user()

    responses = await asyncio.gather(*(api.apply(user, meeting) for _ in range(5)))

    assert sorted(response.status_code for response in responses) == [201, 409, 409, 409, 409]
    assert {response.json()["code"] for response in responses if response.status_code == 409} == {
        "ALREADY_APPLIED"
    }
    await assert_invariant(engine, meeting.id)


async def test_simultaneous_withdrawals_promote_waitlist_in_order(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
) -> None:
    meeting = await create_meeting(organizer, capacity=5, auto_accept=True)
    accepted = [await create_user() for _ in range(5)]
    waiting = [await create_user() for _ in range(10)]
    # Подаём по очереди: порядок подачи задаёт порядок листа ожидания
    for user in accepted + waiting:
        await api.applied(user, meeting)

    responses = await asyncio.gather(*(api.withdraw(user, meeting) for user in accepted))

    assert [response.status_code for response in responses] == [204] * 5
    statuses = await statuses_by_user(engine, meeting)
    assert [statuses[user.id] for user in accepted] == ["withdrawn"] * 5
    assert [statuses[user.id] for user in waiting] == ["accepted"] * 5 + ["waitlist"] * 5
    card = await api.client.get(f"/api/v1/meetings/{meeting.id}")
    assert card.json()["accepted_count"] == 5
    await assert_invariant(engine, meeting.id)


@pytest.mark.parametrize("decision", ["accepted", "rejected"])
async def test_decision_races_with_withdrawal(
    api: Api,
    engine: AsyncEngine,
    organizer: User,
    create_user: CreateUser,
    create_meeting: CreateMeeting,
    decision: str,
) -> None:
    meeting = await create_meeting(organizer)
    user = await create_user()
    application = await api.applied(user, meeting)

    decided, withdrawn = await asyncio.gather(
        api.decide(organizer, application["id"], decision), api.withdraw(user, meeting)
    )

    outcome = (decided.status_code, withdrawn.status_code)
    if decision == "rejected":
        # После отказа отозвать нельзя, после отзыва нельзя решить — ровно один запрос падает
        assert outcome in {(200, 409), (409, 204)}
    else:
        # Принятую заявку отозвать можно, поэтому при порядке «решение → отзыв» оба успешны
        assert outcome in {(200, 204), (409, 204)}
    if decided.status_code == 409:
        assert decided.json()["code"] == "INVALID_TRANSITION"
    if withdrawn.status_code == 409:
        assert withdrawn.json()["code"] == "INVALID_TRANSITION"
    expected = "rejected" if outcome == (200, 409) else "withdrawn"
    assert (await statuses_by_user(engine, meeting))[user.id] == expected
    await assert_invariant(engine, meeting.id)
