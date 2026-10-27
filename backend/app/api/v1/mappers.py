from app.models.application import Application
from app.models.meeting import Meeting
from app.schemas.applications import (
    ApplicantOut,
    ApplicationOut,
)
from app.schemas.enums import ApplicationStatus, GeoStatus, MeetingStatus
from app.schemas.meetings import (
    MeetingListItem,
    MeetingOut,
    MyApplicationOut,
    OrganizerBrief,
    OrganizerOut,
)


def to_meeting_out(meeting: Meeting, my_application: MyApplicationOut | None = None) -> MeetingOut:
    return MeetingOut(
        id=meeting.id,
        status=MeetingStatus[meeting.status.name],
        geo_status=GeoStatus[meeting.geo_status.name],
        title=meeting.title,
        description=meeting.description,
        category=meeting.category.slug,
        starts_at=meeting.starts_at,
        duration_minutes=meeting.duration_minutes,
        address=meeting.address,
        address_hint=meeting.address_hint,
        address_norm=meeting.address_norm,
        lat=meeting.lat,
        lon=meeting.lon,
        capacity=meeting.capacity,
        accepted_count=meeting.accepted_count,
        free_places=meeting.capacity - meeting.accepted_count,
        auto_accept=meeting.auto_accept,
        organizer=OrganizerOut(
            id=meeting.organizer.id,
            display_name=meeting.organizer.display_name,
            attendance_rate=meeting.organizer.attendance_rate,
        ),
        my_application=my_application,
        created_at=meeting.created_at,
    )


def to_meeting_list_item(meeting: Meeting, distance_km: float | None = None) -> MeetingListItem:
    return MeetingListItem(
        id=meeting.id,
        status=MeetingStatus[meeting.status.name],
        geo_status=GeoStatus[meeting.geo_status.name],
        title=meeting.title,
        category=meeting.category.slug,
        starts_at=meeting.starts_at,
        duration_minutes=meeting.duration_minutes,
        address=meeting.address,
        lat=meeting.lat,
        lon=meeting.lon,
        capacity=meeting.capacity,
        accepted_count=meeting.accepted_count,
        free_places=meeting.capacity - meeting.accepted_count,
        organizer=OrganizerBrief(
            id=meeting.organizer.id, display_name=meeting.organizer.display_name
        ),
        distance_km=distance_km,
    )


def to_my_application_out(application: Application) -> MyApplicationOut:
    return MyApplicationOut(id=application.id, status=ApplicationStatus[application.status.name])


def to_application_out(application: Application) -> ApplicationOut:
    return ApplicationOut(
        id=application.id,
        meeting_id=application.meeting_id,
        status=ApplicationStatus[application.status.name],
        message=application.message,
        created_at=application.created_at,
        decided_at=application.decided_at,
        user=ApplicantOut(
            id=application.user.id,
            display_name=application.user.display_name,
            attendance_rate=application.user.attendance_rate,
            attended_count=application.user.attended_count,
        ),
    )
