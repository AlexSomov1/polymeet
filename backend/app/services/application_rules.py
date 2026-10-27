"""Правила заявок: статус при подаче, отзыв, решение организатора, лист ожидания.

Чистые функции без БД и Redis; текущее время передаётся параметром. Кто вызывает правило,
решает роут: отзыв и решение — разные эндпоинты, поэтому «актора» здесь нет.
"""

from dataclasses import dataclass
from datetime import datetime

from app.core.errors import (
    CapacityReachedError,
    ForbiddenError,
    InvalidTransitionError,
    MeetingNotPublishedError,
)
from app.models.enums import ApplicationStatus, MeetingStatus


@dataclass(frozen=True, slots=True)
class TransitionPlan:
    new_status: ApplicationStatus
    delta_accepted: int  # на сколько меняется meetings.accepted_count: -1, 0 или +1


def initial_status(auto_accept: bool, accepted_count: int, capacity: int) -> ApplicationStatus:
    if accepted_count >= capacity:
        return ApplicationStatus.WAITLIST
    return ApplicationStatus.ACCEPTED if auto_accept else ApplicationStatus.PENDING


def check_can_apply(
    meeting_status: MeetingStatus,
    starts_at: datetime,
    now: datetime,
    organizer_id: int,
    user_id: int,
) -> None:
    if organizer_id == user_id:
        raise ForbiddenError("Нельзя подать заявку на свою встречу")
    if meeting_status != MeetingStatus.PUBLISHED or starts_at <= now:
        raise MeetingNotPublishedError()


def withdraw_plan(current: ApplicationStatus) -> TransitionPlan:
    if current in (ApplicationStatus.PENDING, ApplicationStatus.WAITLIST):
        return TransitionPlan(ApplicationStatus.WITHDRAWN, 0)
    if current == ApplicationStatus.ACCEPTED:
        return TransitionPlan(ApplicationStatus.WITHDRAWN, -1)
    raise InvalidTransitionError()


def decide_plan(
    current: ApplicationStatus,
    decision: ApplicationStatus,
    accepted_count: int,
    capacity: int,
) -> TransitionPlan:
    undecided = (ApplicationStatus.PENDING, ApplicationStatus.WAITLIST)
    if decision == ApplicationStatus.ACCEPTED and current in undecided:
        if accepted_count >= capacity:
            raise CapacityReachedError()
        return TransitionPlan(ApplicationStatus.ACCEPTED, 1)
    if decision == ApplicationStatus.REJECTED and current in undecided:
        return TransitionPlan(ApplicationStatus.REJECTED, 0)
    if decision == ApplicationStatus.REJECTED and current == ApplicationStatus.ACCEPTED:
        return TransitionPlan(ApplicationStatus.REJECTED, -1)
    raise InvalidTransitionError()


def promote_count(accepted_count: int, capacity: int, waitlist_len: int) -> int:
    """Сколько заявок из листа ожидания перевести в ``accepted`` (FIFO делает сервис)."""
    return max(0, min(capacity - accepted_count, waitlist_len))
