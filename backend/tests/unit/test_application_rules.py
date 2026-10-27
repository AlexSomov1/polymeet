from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import (
    AppError,
    CapacityReachedError,
    ForbiddenError,
    InvalidTransitionError,
    MeetingNotPublishedError,
)
from app.models.enums import ApplicationStatus, MeetingStatus
from app.services.application_rules import (
    TransitionPlan,
    check_can_apply,
    decide_plan,
    initial_status,
    promote_count,
    withdraw_plan,
)

NOW = datetime(2030, 1, 1, tzinfo=UTC)
CAPACITY = 5
# Сколько уже принято при лимите 5: мест нет, ровно одно место, мест много
ACCEPTED = {"full": 5, "one_left": 4, "many_left": 1}

S = ApplicationStatus
ACCEPT = TransitionPlan(S.ACCEPTED, 1)
REJECT = TransitionPlan(S.REJECTED, 0)


def _decide_expected(
    current: ApplicationStatus, decision: ApplicationStatus, seats: str
) -> TransitionPlan | type[AppError]:
    if current in (S.PENDING, S.WAITLIST):
        if decision == S.REJECTED:
            return REJECT
        return CapacityReachedError if seats == "full" else ACCEPT
    if current == S.ACCEPTED and decision == S.REJECTED:
        return TransitionPlan(S.REJECTED, -1)
    return InvalidTransitionError


@pytest.mark.parametrize("seats", list(ACCEPTED))
@pytest.mark.parametrize("decision", [S.ACCEPTED, S.REJECTED])
@pytest.mark.parametrize("current", list(ApplicationStatus))
def test_decide_matrix(current: ApplicationStatus, decision: ApplicationStatus, seats: str) -> None:
    expected = _decide_expected(current, decision, seats)

    if isinstance(expected, TransitionPlan):
        assert decide_plan(current, decision, ACCEPTED[seats], CAPACITY) == expected
    else:
        with pytest.raises(expected):
            decide_plan(current, decision, ACCEPTED[seats], CAPACITY)


def test_decide_matrix_spells_out_capacity_rule() -> None:
    # Явно, а не через _decide_expected: последнее место можно занять, сверх лимита — нет
    assert decide_plan(S.WAITLIST, S.ACCEPTED, 4, 5) == ACCEPT
    with pytest.raises(CapacityReachedError):
        decide_plan(S.PENDING, S.ACCEPTED, 5, 5)
    # Отказ принятому всегда возможен, даже при заполненной встрече
    assert decide_plan(S.ACCEPTED, S.REJECTED, 5, 5) == TransitionPlan(S.REJECTED, -1)


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (S.PENDING, TransitionPlan(S.WITHDRAWN, 0)),
        (S.WAITLIST, TransitionPlan(S.WITHDRAWN, 0)),
        (S.ACCEPTED, TransitionPlan(S.WITHDRAWN, -1)),
        (S.REJECTED, InvalidTransitionError),
        (S.WITHDRAWN, InvalidTransitionError),
    ],
)
def test_withdraw_matrix(
    current: ApplicationStatus, expected: TransitionPlan | type[AppError]
) -> None:
    if isinstance(expected, TransitionPlan):
        assert withdraw_plan(current) == expected
    else:
        with pytest.raises(expected):
            withdraw_plan(current)


@pytest.mark.parametrize(
    ("auto_accept", "seats", "expected"),
    [
        (True, "full", S.WAITLIST),
        (True, "one_left", S.ACCEPTED),
        (True, "many_left", S.ACCEPTED),
        (False, "full", S.WAITLIST),
        (False, "one_left", S.PENDING),
        (False, "many_left", S.PENDING),
    ],
)
def test_initial_status(auto_accept: bool, seats: str, expected: ApplicationStatus) -> None:
    assert initial_status(auto_accept, ACCEPTED[seats], CAPACITY) == expected


ORGANIZER, APPLICANT = 1, 2


@pytest.mark.parametrize(
    ("status", "starts_at", "user_id", "error"),
    [
        (MeetingStatus.PUBLISHED, NOW + timedelta(hours=1), APPLICANT, None),
        (MeetingStatus.DRAFT, NOW + timedelta(hours=1), APPLICANT, MeetingNotPublishedError),
        (MeetingStatus.CANCELLED, NOW + timedelta(hours=1), APPLICANT, MeetingNotPublishedError),
        (MeetingStatus.FINISHED, NOW + timedelta(hours=1), APPLICANT, MeetingNotPublishedError),
        (MeetingStatus.PUBLISHED, NOW, APPLICANT, MeetingNotPublishedError),
        (MeetingStatus.PUBLISHED, NOW - timedelta(hours=1), APPLICANT, MeetingNotPublishedError),
        (MeetingStatus.PUBLISHED, NOW + timedelta(hours=1), ORGANIZER, ForbiddenError),
        # Своя встреча проверяется первой: даже отменённая даёт FORBIDDEN
        (MeetingStatus.CANCELLED, NOW + timedelta(hours=1), ORGANIZER, ForbiddenError),
        (MeetingStatus.PUBLISHED, NOW - timedelta(hours=1), ORGANIZER, ForbiddenError),
    ],
)
def test_check_can_apply(
    status: MeetingStatus,
    starts_at: datetime,
    user_id: int,
    error: type[AppError] | None,
) -> None:
    if error is None:
        check_can_apply(status, starts_at, NOW, ORGANIZER, user_id)
    else:
        with pytest.raises(error):
            check_can_apply(status, starts_at, NOW, ORGANIZER, user_id)


@pytest.mark.parametrize(
    ("accepted_count", "capacity", "waitlist_len", "expected"),
    [
        (3, 5, 0, 0),  # лист ожидания пуст
        (3, 5, 1, 1),  # в листе меньше, чем свободных мест
        (3, 5, 2, 2),  # ровно
        (3, 5, 7, 2),  # в листе больше
        (5, 5, 4, 0),  # мест нет совсем
    ],
)
def test_promote_count(
    accepted_count: int, capacity: int, waitlist_len: int, expected: int
) -> None:
    assert promote_count(accepted_count, capacity, waitlist_len) == expected
