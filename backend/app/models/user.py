from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, Integer, Numeric, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import CITEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("char_length(display_name) BETWEEN 2 AND 50", name="display_name_length"),
        CheckConstraint("attendance_rate BETWEEN 0 AND 1", name="attendance_rate_range"),
    )
    # Значения по умолчанию задаёт БД; RETURNING сразу подгружает их в объект.
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[str] = mapped_column(String(26), primary_key=True)
    email: Mapped[str] = mapped_column(CITEXT, unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str] = mapped_column(Text)
    role: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    # Счётчики репутации есть в ER-модели, но в этой фазе не используются.
    themes_created: Mapped[int] = mapped_column(Integer, server_default="0")
    themes_attended: Mapped[int] = mapped_column(Integer, server_default="0")
    attendance_rate: Mapped[Decimal] = mapped_column(Numeric(4, 3), server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
