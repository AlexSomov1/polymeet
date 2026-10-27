from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self) -> list[Category]:
        return list(await self._session.scalars(select(Category).order_by(Category.id)))

    async def get_by_slug(self, slug: str) -> Category | None:
        return await self._session.scalar(select(Category).where(Category.slug == slug))
