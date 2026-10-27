from datetime import datetime

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.application import Application
from app.models.enums import ApplicationStatus


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, application: Application) -> Application:
        self._session.add(application)
        await self._session.flush()
        return application

    async def get(self, application_id: int) -> Application | None:
        return await self._session.get(Application, application_id)

    async def get_for_update(self, application_id: int) -> Application | None:
        """Заявка с блокировкой строки; статус перечитывается, даже если она уже в сессии."""
        return await self._session.scalar(
            select(Application)
            .options(joinedload(Application.user, innerjoin=True))
            .where(Application.id == application_id)
            .with_for_update(of=Application)
            .execution_options(populate_existing=True)
        )

    async def get_active(
        self, meeting_id: int, user_id: int, *, for_update: bool = False
    ) -> Application | None:
        """Действующая (не отозванная) заявка пользователя на встречу."""
        query = select(Application).where(
            Application.meeting_id == meeting_id,
            Application.user_id == user_id,
            Application.status != ApplicationStatus.WITHDRAWN,
        )
        if for_update:
            query = query.with_for_update()
        return await self._session.scalar(query)

    async def list_waitlist_for_update(self, meeting_id: int, limit: int) -> list[Application]:
        """Самые ранние заявки листа ожидания (FIFO) с блокировкой строк."""
        return list(
            await self._session.scalars(
                select(Application)
                .where(
                    Application.meeting_id == meeting_id,
                    Application.status == ApplicationStatus.WAITLIST,
                )
                .order_by(Application.created_at, Application.id)
                .limit(limit)
                .with_for_update()
            )
        )

    async def list_for_meeting(
        self,
        meeting_id: int,
        status: ApplicationStatus | None,
        after: tuple[datetime, int] | None,
        limit: int,
    ) -> list[Application]:
        """Очередь организатора в порядке подачи, до ``limit + 1`` заявок."""
        query = (
            select(Application)
            .options(joinedload(Application.user, innerjoin=True))
            .where(Application.meeting_id == meeting_id)
            .order_by(Application.created_at, Application.id)
            .limit(limit + 1)
        )
        if status is not None:
            query = query.where(Application.status == status)
        if after is not None:
            query = query.where(tuple_(Application.created_at, Application.id) > after)
        return list(await self._session.scalars(query))

    async def list_by_user(
        self,
        user_id: int,
        status: ApplicationStatus | None,
        after: tuple[datetime, int] | None,
        limit: int,
    ) -> list[Application]:
        """Заявки пользователя, новые сначала, до ``limit + 1`` штук."""
        query = (
            select(Application)
            .options(joinedload(Application.meeting, innerjoin=True))
            .where(Application.user_id == user_id)
            .order_by(Application.created_at.desc(), Application.id.desc())
            .limit(limit + 1)
        )
        if status is not None:
            query = query.where(Application.status == status)
        if after is not None:
            query = query.where(tuple_(Application.created_at, Application.id) < after)
        return list(await self._session.scalars(query))
