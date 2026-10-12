import base64
import json
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.core.errors import ValidationAppError
from app.core.pagination import decode_cursor, encode_cursor


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def test_cursor_round_trip_restores_typed_keyset() -> None:
    starts_at = datetime(2026, 10, 13, 18, 30, tzinfo=timezone(timedelta(hours=3)))

    cursor = encode_cursor([starts_at, 42])

    assert decode_cursor(cursor, [datetime, int]) == [starts_at, 42]
    assert decode_cursor(cursor, [datetime, int])[0].utcoffset() == timedelta(hours=3)


def test_cursor_is_url_safe_without_padding() -> None:
    cursor = encode_cursor(["Настолки в «Кубе»?&=/+", 10**12])

    assert all(char.isalnum() or char in "-_" for char in cursor)
    assert decode_cursor(cursor) == ["Настолки в «Кубе»?&=/+", 10**12]


@pytest.mark.parametrize(
    ("cursor", "types"),
    [
        ("not a cursor!", None),
        ("%%%", None),
        (_b64(b"\xff\xfe"), None),
        (_b64(b"{not json"), None),
        (_b64(json.dumps({"starts_at": "2026-10-13"}).encode()), None),
        (encode_cursor([datetime(2026, 1, 1, tzinfo=UTC)]), [datetime, int]),
        (encode_cursor(["yesterday", 1]), [datetime, int]),
        (encode_cursor([datetime(2026, 1, 1, tzinfo=UTC), "one"]), [datetime, int]),
    ],
    ids=[
        "garbage",
        "bad_alphabet",
        "not_utf8",
        "not_json",
        "object_instead_of_list",
        "wrong_part_count",
        "bad_datetime",
        "bad_int",
    ],
)
def test_damaged_or_forged_cursor_is_validation_error(
    cursor: str, types: list[type] | None
) -> None:
    with pytest.raises(ValidationAppError) as exc_info:
        decode_cursor(cursor, types)

    assert exc_info.value.http_status == 400
    assert exc_info.value.details == [{"field": "cursor", "message": "Недействительный курсор"}]
