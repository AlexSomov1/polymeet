"""Заявки на участие: подача, отзыв, решение организатора, лист ожидания.

Каждая запись — одна транзакция, которая начинается с блокировки строки встречи
(``SELECT … FOR UPDATE``). Блокировка сериализует изменения заявок встречи и счётчика
``accepted_count``, поэтому лишний участник сверх лимита пройти не может.
"""

from datetime import UTC, datetime

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import is_unique_violation
from app.core.errors import (
    AlreadyAppliedError,
    ForbiddenError,
    InvalidTransitionError,
    NotFoundError,
    ValidationAppError,
)
from app.core.pagination import decode_cursor, encode_cursor
from app.models.application import Application
from app.models.enums import ApplicationStatus, MeetingStatus
from app.models.meeting import Meeting
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.meeting_repository import MeetingRepository
from app.services.application_rules import (
    TransitionPlan,
    check_can_apply,
    decide_plan,
    initial_status,
    promote_count,
    withdraw_plan,
)
from app.services.meeting_rules import can_view

logger = structlog.get_logger(__name__)


def _meeting_not_found() -> NotFoundError:
    return NotFoundError("Встреча не найдена")


def _decode_cursor(cursor: str | None) -> tuple[datetime, int] | None:
    if cursor is None:
        return None
    created_at, application_id = decode_cursor(cursor, [datetime, int])
    if created_at.tzinfo is None or application_id <= 0:
        raise ValidationAppError.for_field("cursor", "Недействительный курсор")
    return created_at, application_id


def _page(applications: list[Application], limit: int) -> tuple[list[Application], str | None]:
    items = applications[:limit]
    if len(applications) <= limit:
        return items, None
    return items, encode_cursor([items[-1].created_at, items[-1].id])


async def promote_waitlist(session: AsyncSession, meeting: Meeting) -> int:
    """Переводит самые ранние заявки листа ожидания на свободные места.

    Вызывается только внутри транзакции, где строка встречи уже заблокирована.
    Возвращает число продвинутых заявок.
    """
    now = datetime.now(UTC)
    free = meeting.capacity - meeting.accepted_count
    if meeting.status != MeetingStatus.PUBLISHED or meeting.starts_at <= now or free <= 0:
        return 0
    waitlist = await ApplicationRepository(session).list_waitlist_for_update(meeting.id, free)
    count = promote_count(meeting.accepted_count, meeting.capacity, len(waitlist))
    for application in waitlist[:count]:
        application.status = ApplicationStatus.ACCEPTED
        application.decided_at = now
    meeting.accepted_count += count
    return count


class ApplicationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._applications = ApplicationRepository(session)
        self._meetings = MeetingRepository(session)

    async def _lock_visible_meeting(self, meeting_id: int, viewer: User) -> Meeting:
        meeting = await self._meetings.get_for_update(meeting_id)
        if meeting is None or not can_view(meeting.status, meeting.organizer_id, viewer.id):
            raise _meeting_not_found()
        return meeting

    async def _apply_plan(
        self, meeting: Meeting, application: Application, plan: TransitionPlan
    ) -> int:
        """Записывает переход и, если место освободилось, продвигает лист ожидания."""
        application.status = plan.new_status
        application.decided_at = datetime.now(UTC)
        meeting.accepted_count += plan.delta_accepted
        if plan.delta_accepted < 0:
            return await promote_waitlist(self._session, meeting)
        return 0

    async def apply(self, user: User, meeting_id: int, message: str | None) -> Application:
        meeting = await self._lock_visible_meeting(meeting_id, user)
        now = datetime.now(UTC)
        check_can_apply(meeting.status, meeting.starts_at, now, meeting.organizer_id, user.id)
        status = initial_status(meeting.auto_accept, meeting.accepted_count, meeting.capacity)
        application = Application(
            meeting_id=meeting.id,
            user=user,
            status=status,
            message=(message or "").strip() or None,
            decided_at=now if status == ApplicationStatus.ACCEPTED else None,
        )
        # Предварительной проверки нет: повторную заявку отсекает уникальный индекс.
        try:
            await self._applications.add(application)
        except IntegrityError as exc:
            await self._session.rollback()
            if is_unique_violation(exc):
                raise AlreadyAppliedError() from exc
            raise
        if status == ApplicationStatus.ACCEPTED:
            meeting.accepted_count += 1
        await self._session.commit()
        logger.info(
            "application_created",
            application_id=application.id,
            meeting_id=meeting.id,
            status=status.name.lower(),
        )
        return application

    async def withdraw(self, user: User, meeting_id: int) -> None:
        meeting = await self._lock_visible_meeting(meeting_id, user)
        application = await self._applications.get_active(meeting.id, user.id, for_update=True)
        if application is None:
            raise NotFoundError("Заявка не найдена")
        old_status = application.status
        promoted = await self._apply_plan(meeting, application, withdraw_plan(old_status))
        await self._session.commit()
        logger.info(
            "application_withdrawn",
            application_id=application.id,
            old_status=old_status.name.lower(),
            new_status=application.status.name.lower(),
            promoted=promoted,
        )

    async def decide(
        self, actor: User, application_id: int, decision: ApplicationStatus
    ) -> Application:
        found = await self._applications.get(application_id)
        if found is None:
            raise NotFoundError("Заявка не найдена")
        meeting = await self._meetings.get_for_update(found.meeting_id)
        if meeting is None:
            raise NotFoundError("Заявка не найдена")
        if meeting.organizer_id != actor.id:
            raise ForbiddenError()
        # Пока ждали блокировку встречи, статус заявки мог измениться
        application = await self._applications.get_for_update(application_id)
        if application is None:
            raise NotFoundError("Заявка не найдена")
        if meeting.status != MeetingStatus.PUBLISHED:
            raise InvalidTransitionError("Решения по неопубликованной встрече не принимаются")
        old_status = application.status
        plan = decide_plan(old_status, decision, meeting.accepted_count, meeting.capacity)
        promoted = await self._apply_plan(meeting, application, plan)
        await self._session.commit()
        logger.info(
            "application_decided",
            application_id=application.id,
            old_status=old_status.name.lower(),
            new_status=application.status.name.lower(),
            promoted=promoted,
        )
        return application

    async def list_for_organizer(
        self,
        actor: User,
        meeting_id: int,
        status: ApplicationStatus | None,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[Application], str | None]:
        meeting = await self._meetings.get(meeting_id)
        if meeting is None or not can_view(meeting.status, meeting.organizer_id, actor.id):
            raise _meeting_not_found()
        if meeting.organizer_id != actor.id:
            raise ForbiddenError()
        after = _decode_cursor(cursor)
        applications = await self._applications.list_for_meeting(meeting.id, status, after, limit)
        return _page(applications, limit)

    async def list_mine(
        self, user: User, status: ApplicationStatus | None, cursor: str | None, limit: int
    ) -> tuple[list[Application], str | None]:
        after = _decode_cursor(cursor)
        applications = await self._applications.list_by_user(user.id, status, after, limit)
        return _page(applications, limit)

    async def get_my_application(self, meeting_id: int, user: User) -> Application | None:
        """Действующая заявка: после отзыва пользователь снова видит «подать заявку»."""
        return await self._applications.get_active(meeting_id, user.id)
