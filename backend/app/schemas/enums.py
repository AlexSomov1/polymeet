"""Строковые перечисления API. Имена совпадают с ``app.models.enums``."""

from enum import StrEnum


class MeetingStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    FINISHED = "finished"


class GeoStatus(StrEnum):
    PENDING = "pending"
    RESOLVED = "resolved"
    MANUAL = "manual"
    FAILED = "failed"


class ApplicationStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITLIST = "waitlist"
    WITHDRAWN = "withdrawn"


class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    EMAIL_TAKEN = "EMAIL_TAKEN"
    ALREADY_APPLIED = "ALREADY_APPLIED"
    CAPACITY_REACHED = "CAPACITY_REACHED"
    INVALID_TRANSITION = "INVALID_TRANSITION"
    MEETING_NOT_PUBLISHED = "MEETING_NOT_PUBLISHED"
    RATE_LIMITED = "RATE_LIMITED"
    HTTP_ERROR = "HTTP_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
