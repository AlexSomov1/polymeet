import pytest
from sqlalchemy import func, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.models.application import Application
from app.models.enums import ApplicationStatus
from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from tests.integration.helpers import CreateMeeting, CreateUser


@pytest.fixture
async def meeting(create_user: CreateUser, create_meeting: CreateMeeting) -> Meeting:
    return await create_meeting(await create_user())


@pytest.fixture
async def applicant(create_user: CreateUser) -> User:
    return await create_user()


async def _apply(
    engine: AsyncEngine,
    meeting: Meeting,
    user: User,
    status: ApplicationStatus = ApplicationStatus.PENDING,
    message: str | None = None,
) -> Application:
    async with AsyncSession(engine, expire_on_commit=False) as session:
        application = await ApplicationRepository(session).add(
            Application(meeting_id=meeting.id, user_id=user.id, status=status, message=message)
        )
        await session.commit()
    return application


async def _set_status(engine: AsyncEngine, application_id: int, status: ApplicationStatus) -> None:
    async with AsyncSession(engine) as session:
        await session.execute(
            update(Application).where(Application.id == application_id).values(status=status)
        )
        await session.commit()


async def test_repository_round_trip(
    engine: AsyncEngine, meeting: Meeting, applicant: User
) -> None:
    created = await _apply(engine, meeting, applicant, message="Возьму доску")

    async with AsyncSession(engine) as session:
        loaded = await ApplicationRepository(session).get(created.id)
    assert loaded is not None
    assert (loaded.status, loaded.message, loaded.decided_at) == (
        ApplicationStatus.PENDING,
        "Возьму доску",
        None,
    )
    assert loaded.created_at is not None


async def test_only_one_active_application_per_meeting(
    engine: AsyncEngine, meeting: Meeting, applicant: User
) -> None:
    await _apply(engine, meeting, applicant)

    with pytest.raises(IntegrityError, match="uq_applications_once"):
        await _apply(engine, meeting, applicant, ApplicationStatus.WAITLIST)


async def test_withdrawn_frees_the_slot_but_rejected_does_not(
    engine: AsyncEngine, meeting: Meeting, applicant: User, create_user: CreateUser
) -> None:
    first = await _apply(engine, meeting, applicant)
    await _set_status(engine, first.id, ApplicationStatus.WITHDRAWN)
    second = await _apply(engine, meeting, applicant)

    await _set_status(engine, second.id, ApplicationStatus.REJECTED)
    with pytest.raises(IntegrityError, match="uq_applications_once"):
        await _apply(engine, meeting, applicant)

    # Ограничение — на пару (встреча, пользователь): другой пользователь подаёт свободно
    await _apply(engine, meeting, await create_user())


@pytest.mark.parametrize(
    ("column", "value", "constraint"),
    [
        ("status", "5", "ck_applications_status"),
        ("message", "repeat('я', 301)", "ck_applications_message_length"),
    ],
)
async def test_check_constraints(
    engine: AsyncEngine,
    meeting: Meeting,
    applicant: User,
    column: str,
    value: str,
    constraint: str,
) -> None:
    application = await _apply(engine, meeting, applicant)

    with pytest.raises(IntegrityError, match=constraint):
        async with engine.begin() as conn:
            await conn.execute(
                text(f"UPDATE applications SET {column} = {value} WHERE id = :id"),
                {"id": application.id},
            )


async def test_message_of_300_chars_fits(
    engine: AsyncEngine, meeting: Meeting, applicant: User
) -> None:
    await _apply(engine, meeting, applicant, message="я" * 300)


async def test_deleting_meeting_deletes_its_applications(
    engine: AsyncEngine, meeting: Meeting, applicant: User, create_user: CreateUser
) -> None:
    await _apply(engine, meeting, applicant)
    await _apply(engine, meeting, await create_user())

    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM meetings WHERE id = :id"), {"id": meeting.id})
        remaining = await conn.scalar(select(func.count()).select_from(Application))
    assert remaining == 0
