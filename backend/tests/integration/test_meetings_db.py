from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from app.models.user import User
from tests.integration.helpers import CreateUser


@pytest.mark.parametrize(
    "column,value",
    [
        ("capacity", "1"),
        ("capacity", "101"),
        ("accepted_count", "101"),
        ("duration_minutes", "10"),
        ("title", "'Я'"),
        ("lat", "59.9"),
    ],
)
async def test_database_checks_reject_invalid_meetings(
    engine: AsyncEngine, create_user: CreateUser, column: str, value: str
) -> None:
    user: User = await create_user()
    starts_at = datetime.now(UTC) + timedelta(days=1)
    async with engine.begin() as conn:
        meeting_id = await conn.scalar(
            text(
                "INSERT INTO meetings (organizer_id, category_id, title, starts_at, "
                "duration_minutes, address, capacity) "
                "VALUES (:organizer_id, 2, 'Настолки', :starts_at, 60, 'Литейный 12', 6) "
                "RETURNING id"
            ),
            {"organizer_id": user.id, "starts_at": starts_at},
        )
        with pytest.raises(IntegrityError):
            await conn.execute(
                text(f"UPDATE meetings SET {column} = {value} WHERE id = :id"),
                {"id": meeting_id},
            )
