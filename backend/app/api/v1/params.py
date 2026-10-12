"""Общие параметры роутов v1 и описание целевого времени ответа (README, раздел 3.3)."""

from typing import Annotated

from fastapi import Path, Query

Cursor = Annotated[
    str | None,
    Query(max_length=512, description="`next_cursor` из предыдущей страницы"),
]
PageLimit = Annotated[int, Query(ge=1, le=50, description="Размер страницы")]
MeetingId = Annotated[int, Path(ge=1, description="id встречи")]
UserId = Annotated[int, Path(ge=1, description="id пользователя")]
ApplicationId = Annotated[int, Path(ge=1, description="id заявки")]


def p95(ms: int, text: str = "") -> str:
    """Описание операции с целевым временем ответа."""
    target = f"Целевое время ответа: p95 ≤ {ms} мс."
    return f"{text}\n\n{target}" if text else target
