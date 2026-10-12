"""Перечисления в базе (``smallint``). В API те же значения передаются строками
в нижнем регистре: см. ``app.schemas.enums``."""

from enum import IntEnum


class MeetingStatus(IntEnum):
    DRAFT = 0
    PUBLISHED = 1
    CANCELLED = 2
    FINISHED = 3


class GeoStatus(IntEnum):
    PENDING = 0
    RESOLVED = 1
    MANUAL = 2
    FAILED = 3


class ApplicationStatus(IntEnum):
    PENDING = 0
    ACCEPTED = 1
    REJECTED = 2
    WAITLIST = 3
    WITHDRAWN = 4
