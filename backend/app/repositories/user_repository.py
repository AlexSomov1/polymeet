from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def create(
        self, *, email: str, password_hash: str, display_name: str, role: int = 0
    ) -> User:
        """Добавляет пользователя и выполняет flush; нарушение уникальности e-mail
        поднимается здесь как ``IntegrityError``. Коммит — забота вызывающего."""
        user = User(
            email=email,
            password_hash=password_hash,
            display_name=display_name,
            role=role,
        )
        self._session.add(user)
        await self._session.flush()
        return user
