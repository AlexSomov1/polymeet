from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
