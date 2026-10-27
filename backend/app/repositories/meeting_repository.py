from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.meeting import Meeting


class MeetingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, meeting: Meeting) -> Meeting:
        self._session.add(meeting)
        await self._session.flush()
        return meeting

    async def get(self, meeting_id: int) -> Meeting | None:
        return await self._session.scalar(
            select(Meeting)
            .options(joinedload(Meeting.organizer), joinedload(Meeting.category))
            .where(Meeting.id == meeting_id)
        )

    async def get_for_update(self, meeting_id: int) -> Meeting | None:
        return await self._session.scalar(
            select(Meeting)
            .options(
                joinedload(Meeting.organizer, innerjoin=True),
                joinedload(Meeting.category, innerjoin=True),
            )
            .where(Meeting.id == meeting_id)
            .with_for_update(of=Meeting)
        )

    async def list_by_organizer(
        self, organizer_id: int, after: tuple[datetime, int] | None, limit: int
    ) -> list[Meeting]:
        query = (
            select(Meeting)
            .options(joinedload(Meeting.organizer), joinedload(Meeting.category))
            .where(Meeting.organizer_id == organizer_id)
            .order_by(Meeting.created_at.desc(), Meeting.id.desc())
            .limit(limit + 1)
        )
        if after is not None:
            query = query.where(tuple_(Meeting.created_at, Meeting.id) < after)
        return list(await self._session.scalars(query))
