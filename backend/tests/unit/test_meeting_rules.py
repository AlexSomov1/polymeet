from datetime import UTC, datetime, timedelta

import pytest

from app.core.errors import InvalidTransitionError, ValidationAppError
from app.models.enums import MeetingStatus
from app.services.meeting_rules import (
    can_view,
    check_capacity,
    check_starts_at,
    check_transition,
    normalize_address,
    normalize_address_hint,
    normalize_title,
)

NOW = datetime(2030, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize("current", list(MeetingStatus))
@pytest.mark.parametrize("target", list(MeetingStatus))
@pytest.mark.parametrize("future", [True, False])
def test_transition_matrix(current: MeetingStatus, target: MeetingStatus, future: bool) -> None:
    starts_at = NOW + (timedelta(minutes=1) if future else -timedelta(minutes=1))
    allowed = (current, target) in {
        (MeetingStatus.DRAFT, MeetingStatus.PUBLISHED),
        (MeetingStatus.DRAFT, MeetingStatus.CANCELLED),
        (MeetingStatus.PUBLISHED, MeetingStatus.CANCELLED),
    }
    if not allowed:
        with pytest.raises(InvalidTransitionError):
            check_transition(current, target, starts_at, NOW)
    elif target == MeetingStatus.PUBLISHED and not future:
        with pytest.raises(ValidationAppError) as error:
            check_transition(current, target, starts_at, NOW)
        assert error.value.details == [
            {"field": "starts_at", "message": "Время начала должно быть в будущем"}
        ]
    else:
        assert check_transition(current, target, starts_at, NOW) == target


@pytest.mark.parametrize("status", list(MeetingStatus))
@pytest.mark.parametrize("viewer_id", [None, 1, 2])
def test_visibility(status: MeetingStatus, viewer_id: int | None) -> None:
    assert can_view(status, organizer_id=1, viewer_id=viewer_id) == (
        status != MeetingStatus.DRAFT or viewer_id == 1
    )


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_capacity_cannot_fall_below_accepted_count(delta: int) -> None:
    if delta < 0:
        with pytest.raises(ValidationAppError):
            check_capacity(5 + delta, 5)
    else:
        check_capacity(5 + delta, 5)


@pytest.mark.parametrize("offset", [-1, 0, 1])
def test_start_must_be_strictly_future(offset: int) -> None:
    if offset <= 0:
        with pytest.raises(ValidationAppError):
            check_starts_at(NOW + timedelta(seconds=offset), NOW)
    else:
        check_starts_at(NOW + timedelta(seconds=offset), NOW)


def test_strings_are_trimmed_and_empty_hint_is_null() -> None:
    assert normalize_title("  Кино  ") == "Кино"
    assert normalize_address("  Невский 1  ") == "Невский 1"
    assert normalize_address_hint("  ") is None
    assert normalize_address_hint("  вход справа  ") == "вход справа"


@pytest.mark.parametrize(
    "normalize,value,field",
    [
        (normalize_title, "  Я  ", "title"),
        (normalize_address, "  1  ", "address"),
    ],
)
def test_short_string_after_trimming_is_rejected(normalize: object, value: str, field: str) -> None:
    with pytest.raises(ValidationAppError) as error:
        normalize(value)  # type: ignore[operator]
    assert error.value.details is not None
    assert error.value.details[0]["field"] == field
