"""Event service — owns all event business logic."""
from datetime import date
from django.db.models import F, QuerySet
from django.utils import timezone

from community.models import FitnessEvent, EventAttendee
from .geo_service import filter_qs_by_radius, attach_distance, DEFAULT_RADIUS_KM


# ── Queries ────────────────────────────────────────────────────────────────────

def get_public_events(activity_type: str = None, city: str = None,
                       from_date: date = None) -> QuerySet:
    qs = FitnessEvent.objects.filter(
        privacy='public', status__in=['upcoming', 'ongoing']
    ).select_related('organizer', 'organizer__creator_profile')

    if activity_type:
        qs = qs.filter(activity_type=activity_type)
    if city:
        qs = qs.filter(city__icontains=city)
    if from_date:
        qs = qs.filter(event_date__gte=from_date)
    else:
        qs = qs.filter(event_date__gte=date.today())

    return qs.order_by('event_date', 'start_time')


def get_nearby_events(lat: float, lon: float, radius_km: float = DEFAULT_RADIUS_KM,
                       activity_type: str = None) -> list:
    qs = get_public_events(activity_type=activity_type)
    qs = filter_qs_by_radius(qs, lat, lon, radius_km)
    return attach_distance(list(qs), lat, lon, radius_km=radius_km)


def get_user_events(user) -> dict:
    organised = FitnessEvent.objects.filter(organizer=user).order_by('-created_at')
    attending_ids = EventAttendee.objects.filter(
        user=user, rsvp_status='going'
    ).values_list('event_id', flat=True)
    attending = FitnessEvent.objects.filter(id__in=attending_ids).exclude(organizer=user)
    return {'organised': organised, 'attending': attending}


# ── Mutations ──────────────────────────────────────────────────────────────────

def create_event(organizer, validated_data: dict) -> FitnessEvent:
    event = FitnessEvent.objects.create(organizer=organizer, **validated_data)
    # Organiser auto-attends
    EventAttendee.objects.create(event=event, user=organizer, rsvp_status='going')
    FitnessEvent.objects.filter(pk=event.pk).update(attendees_count=1)
    return event


def rsvp_event(event: FitnessEvent, user, rsvp_status: str = 'going') -> dict:
    if event.status == 'cancelled':
        raise ValueError("This event has been cancelled.")
    if event.event_date < date.today():
        raise ValueError("Cannot RSVP to a past event.")

    attendee, created = EventAttendee.objects.get_or_create(
        event=event, user=user, defaults={'rsvp_status': rsvp_status}
    )

    if not created:
        # Already RSVP'd — update or withdraw
        if attendee.rsvp_status == rsvp_status:
            # Toggle off: remove RSVP
            attendee.delete()
            if rsvp_status == 'going':
                FitnessEvent.objects.filter(pk=event.pk).update(
                    attendees_count=F('attendees_count') - 1
                )
            return {'rsvp': None, 'action': 'withdrawn'}

        old_was_going = attendee.rsvp_status == 'going'
        attendee.rsvp_status = rsvp_status
        attendee.save(update_fields=['rsvp_status'])
        if old_was_going and rsvp_status != 'going':
            FitnessEvent.objects.filter(pk=event.pk).update(
                attendees_count=F('attendees_count') - 1
            )
        elif not old_was_going and rsvp_status == 'going':
            if event.is_full:
                raise ValueError("Event is full.")
            FitnessEvent.objects.filter(pk=event.pk).update(
                attendees_count=F('attendees_count') + 1
            )
    else:
        if rsvp_status == 'going':
            if event.is_full:
                attendee.delete()
                raise ValueError("Event is full.")
            FitnessEvent.objects.filter(pk=event.pk).update(
                attendees_count=F('attendees_count') + 1
            )

    event.refresh_from_db(fields=['attendees_count'])
    return {'rsvp': rsvp_status, 'attendees_count': event.attendees_count, 'action': 'updated'}


def cancel_event(event: FitnessEvent, user) -> FitnessEvent:
    if event.organizer != user:
        raise PermissionError("Only the organiser can cancel this event.")
    if event.status == 'cancelled':
        raise ValueError("Event is already cancelled.")
    event.status = 'cancelled'
    event.save(update_fields=['status'])
    return event
