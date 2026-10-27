from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ApplicationStatus
from app.models.meeting import IntEnumType, Meeting
from app.models.user import User


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        CheckConstraint("status BETWEEN 0 AND 4", name="status"),
        CheckConstraint("char_length(message) <= 300", name="message_length"),
        # Одна действующая заявка на встречу: после отзыва (4) можно подать снова,
        # после отказа — нельзя.
        Index(
            "uq_applications_once",
            "meeting_id",
            "user_id",
            unique=True,
            postgresql_where=text("status <> 4"),
        ),
        # Очередь организатора и лист ожидания в порядке подачи
        Index("ix_applications_queue", "meeting_id", "status", "created_at", "id"),
        Index("ix_applications_user", "user_id", text("created_at DESC"), text("id DESC")),
    )
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    meeting_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("meetings.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    status: Mapped[ApplicationStatus] = mapped_column(IntEnumType(ApplicationStatus))
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # Время последней смены статуса после подачи
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    meeting: Mapped[Meeting] = relationship(lazy="raise")
    user: Mapped[User] = relationship(lazy="raise")
