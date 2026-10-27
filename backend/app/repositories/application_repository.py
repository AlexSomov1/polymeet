from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, application: Application) -> Application:
        self._session.add(application)
        await self._session.flush()
        return application

    async def get(self, application_id: int) -> Application | None:
        return await self._session.get(Application, application_id)
