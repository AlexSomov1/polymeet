from datetime import datetime

from app.core.errors import InvalidTransitionError, ValidationAppError
from app.models.enums import MeetingStatus


def can_view(status: MeetingStatus, organizer_id: int, viewer_id: int | None) -> bool:
    return status != MeetingStatus.DRAFT or organizer_id == viewer_id


def check_starts_at(starts_at: datetime, now: datetime) -> None:
    if starts_at <= now:
        raise ValidationAppError.for_field("starts_at", "Время начала должно быть в будущем")


def check_capacity(capacity: int, accepted_count: int) -> None:
    if capacity < accepted_count:
        raise ValidationAppError.for_field("capacity", "Лимит меньше числа принятых участников")


def check_transition(
    current: MeetingStatus, target: MeetingStatus, starts_at: datetime, now: datetime
) -> MeetingStatus:
    allowed = {
        (MeetingStatus.DRAFT, MeetingStatus.PUBLISHED),
        (MeetingStatus.DRAFT, MeetingStatus.CANCELLED),
        (MeetingStatus.PUBLISHED, MeetingStatus.CANCELLED),
    }
    if (current, target) not in allowed:
        raise InvalidTransitionError()
    if target == MeetingStatus.PUBLISHED:
        check_starts_at(starts_at, now)
    return target


def normalize_title(value: str) -> str:
    result = value.strip()
    if len(result) < 3:
        raise ValidationAppError.for_field(
            "title", "Название должно содержать не меньше 3 символов"
        )
    return result


def normalize_address(value: str) -> str:
    result = value.strip()
    if len(result) < 3:
        raise ValidationAppError.for_field("address", "Адрес должен содержать не меньше 3 символов")
    return result


def normalize_address_hint(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None
