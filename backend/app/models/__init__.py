"""ORM-модели. Импорт здесь регистрирует их в ``Base.metadata`` для Alembic."""

from app.models.base import Base
from app.models.user import User

__all__ = ["Base", "User"]
