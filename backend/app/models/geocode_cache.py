from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Identity, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class GeocodeCache(Base):
    __tablename__ = "geocode_cache"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    query_hash: Mapped[str] = mapped_column(Text, unique=True)
    query: Mapped[str] = mapped_column(Text)
    address_norm: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float(precision=53))
    lon: Mapped[float] = mapped_column(Float(precision=53))
    hit_count: Mapped[int] = mapped_column(Integer, server_default="0")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
