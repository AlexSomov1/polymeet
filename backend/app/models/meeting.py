from datetime import datetime
from enum import IntEnum
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Computed,
    DateTime,
    Float,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

from app.models.base import Base
from app.models.category import Category
from app.models.enums import GeoStatus, MeetingStatus
from app.models.user import User


class IntEnumType(TypeDecorator[IntEnum]):
    impl = SmallInteger
    cache_ok = True

    def __init__(self, enum_type: type[IntEnum]) -> None:
        super().__init__()
        self.enum_type = enum_type

    def process_bind_param(self, value: IntEnum | int | None, dialect: Any) -> int | None:
        return int(value) if value is not None else None

    def process_result_value(self, value: int | None, dialect: Any) -> IntEnum | None:
        return self.enum_type(value) if value is not None else None


class Meeting(Base):
    __tablename__ = "meetings"
    __table_args__ = (
        CheckConstraint("status BETWEEN 0 AND 3", name="status"),
        CheckConstraint("char_length(title) BETWEEN 3 AND 120", name="title_length"),
        CheckConstraint("char_length(description) <= 2000", name="description_length"),
        CheckConstraint("duration_minutes BETWEEN 15 AND 720", name="duration_minutes"),
        CheckConstraint("char_length(address) BETWEEN 3 AND 300", name="address_length"),
        CheckConstraint("char_length(address_hint) <= 200", name="address_hint_length"),
        CheckConstraint("(lat IS NULL) = (lon IS NULL)", name="coordinates_together"),
        CheckConstraint("lat BETWEEN -90 AND 90", name="latitude"),
        CheckConstraint("lon BETWEEN -180 AND 180", name="longitude"),
        CheckConstraint("geo_status BETWEEN 0 AND 3", name="geo_status"),
        CheckConstraint("capacity BETWEEN 2 AND 100", name="capacity"),
        CheckConstraint("accepted_count BETWEEN 0 AND capacity", name="accepted_count"),
        Index("ix_meetings_feed", "starts_at", "id", postgresql_where=text("status = 1")),
        Index(
            "ix_meetings_category_feed",
            "category_id",
            "starts_at",
            "id",
            postgresql_where=text("status = 1"),
        ),
        Index(
            "ix_meetings_geo",
            func.ll_to_earth(text("lat"), text("lon")),
            postgresql_using="gist",
            postgresql_where=text("status = 1 AND lat IS NOT NULL"),
        ),
        Index("ix_meetings_search", "search_vector", postgresql_using="gin"),
        Index("ix_meetings_organizer", "organizer_id", text("created_at DESC"), text("id DESC")),
    )
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    organizer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    category_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("categories.id"))
    status: Mapped[MeetingStatus] = mapped_column(IntEnumType(MeetingStatus), server_default="0")
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text, server_default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(SmallInteger)
    address: Mapped[str] = mapped_column(Text)
    address_hint: Mapped[str | None] = mapped_column(Text)
    address_norm: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float | None] = mapped_column(Float(precision=53))
    lon: Mapped[float | None] = mapped_column(Float(precision=53))
    geo_status: Mapped[GeoStatus] = mapped_column(IntEnumType(GeoStatus), server_default="0")
    capacity: Mapped[int] = mapped_column(SmallInteger)
    accepted_count: Mapped[int] = mapped_column(SmallInteger, server_default="0")
    auto_accept: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('russian', title || ' ' || description)", persisted=True),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    organizer: Mapped[User] = relationship(lazy="raise")
    category: Mapped[Category] = relationship(lazy="raise")
