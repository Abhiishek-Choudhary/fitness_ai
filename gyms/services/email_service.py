"""
Email service — Single Responsibility: find nearby users and send
gym email campaigns via Django's mail backend.
"""
import logging

from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone

from community.models import UserLocation
from community.services.geo_service import filter_qs_by_radius, haversine

logger = logging.getLogger(__name__)


def find_users_in_area(lat: float, lon: float, radius_km: float) -> list:
    """
    Return User objects whose public location falls within radius_km.
    Excludes hidden-visibility users to respect privacy settings.
    """
    locs = filter_qs_by_radius(
        UserLocation.objects.exclude(visibility='hidden').select_related('user'),
        lat, lon, radius_km
    )
    users = []
    for loc in locs:
        if loc.latitude is None or loc.longitude is None:
            continue
        dist = haversine(lat, lon, float(loc.latitude), float(loc.longitude))
        if dist <= radius_km and loc.user.email:
            users.append(loc.user)
    return users


def send_campaign(gym, campaign) -> int:
    """
    Dispatch an email campaign to users near the gym.
    Updates campaign.sent_at and campaign.sent_to_count in place.
    Returns the number of recipients actually emailed.
    """
    if not gym.latitude or not gym.longitude:
        return 0

    users = find_users_in_area(
        float(gym.latitude),
        float(gym.longitude),
        float(campaign.target_radius_km),
    )

    recipient_emails = list({u.email for u in users if u.email})
    if not recipient_emails:
        return 0

    subject = f"[{gym.name}] {campaign.subject}"
    body = _build_body(gym, campaign)

    try:
        # bcc, not recipient_list: campaign members must not see each other's addresses.
        EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[settings.DEFAULT_FROM_EMAIL],
            bcc=recipient_emails,
        ).send(fail_silently=False)
    except Exception:
        logger.exception('Campaign %s for gym %s failed to send', campaign.pk, gym.pk)
        return 0

    campaign.sent_at = timezone.now()
    campaign.sent_to_count = len(recipient_emails)
    campaign.save(update_fields=['sent_at', 'sent_to_count'])

    return len(recipient_emails)


def _build_body(gym, campaign) -> str:
    contact_lines = []
    if gym.phone:
        contact_lines.append(f"Phone: {gym.phone}")
    if gym.email:
        contact_lines.append(f"Email: {gym.email}")
    if gym.website:
        contact_lines.append(f"Website: {gym.website}")

    contact_block = "\n".join(contact_lines) if contact_lines else ""
    footer = (
        f"\n\n---\n{gym.name}\n{gym.address}, {gym.city}, {gym.state}\n{contact_block}"
        "\n\nYou received this because your location is near this gym."
        "\nTo stop receiving emails, update your location visibility in FitnessAI settings."
    )
    return campaign.body + footer
