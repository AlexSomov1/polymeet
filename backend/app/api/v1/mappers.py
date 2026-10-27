from app.models.meeting import Meeting
from app.schemas.enums import GeoStatus, MeetingStatus
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
