"""Курсоры keyset-пагинации: непрозрачная base64url-строка с JSON-списком значений.

Пример: курсор ленты кодирует ``(starts_at, id)`` последней выданной встречи::

    cursor = encode_cursor([meeting.starts_at, meeting.id])
    starts_at, meeting_id = decode_cursor(cursor, [datetime, int])
"""

import base64
import binascii
import json
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.core.errors import ValidationAppError

CursorPart = str | int | float | bool | datetime | None


def encode_cursor(parts: Sequence[CursorPart]) -> str:
    values = [part.isoformat() if isinstance(part, datetime) else part for part in parts]
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=False).encode()
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")


_adapters: dict[type[Any], TypeAdapter[Any]] = {}


def _adapter(type_: type[Any]) -> TypeAdapter[Any]:
    if type_ not in _adapters:
        _adapters[type_] = TypeAdapter(type_)
    return _adapters[type_]


def _invalid_cursor() -> ValidationAppError:
    return ValidationAppError.for_field("cursor", "Недействительный курсор")


def decode_cursor(cursor: str, types: Sequence[type[Any]] | None = None) -> list[Any]:
    """Разбирает курсор. С ``types`` проверяет число частей и приводит их к типам.

    Повреждённый или подделанный курсор — ``VALIDATION_ERROR`` по полю ``cursor``.
    """
    try:
        raw = base64.b64decode(cursor + "=" * (-len(cursor) % 4), altchars=b"-_", validate=True)
        parts = json.loads(raw)
    except (binascii.Error, ValueError) as exc:
        raise _invalid_cursor() from exc
    if not isinstance(parts, list):
        raise _invalid_cursor()
    if types is None:
        return parts
    if len(parts) != len(types):
        raise _invalid_cursor()
    try:
        return [
            _adapter(type_).validate_python(part) for type_, part in zip(types, parts, strict=True)
        ]
    except ValidationError as exc:
        raise _invalid_cursor() from exc
