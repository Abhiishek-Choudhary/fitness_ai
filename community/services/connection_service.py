"""Connection service — manages user connections and discovery."""
from django.utils import timezone
from django.db.models import Q, QuerySet

from community.models import ConnectionRequest, UserConnection, UserLocation
from .geo_service import filter_qs_by_radius, attach_distance, DEFAULT_RADIUS_KM


# ── Discovery ──────────────────────────────────────────────────────────────────

def get_nearby_people(user, radius_km: float = DEFAULT_RADIUS_KM,
                       activity: str = None) -> list:
    """
    Return a list of UserLocation objects near the requesting user,
    respecting visibility settings. Attaches .distance_km to each.
    """
    try:
        my_loc = user.location
    except UserLocation.DoesNotExist:
        return []

    if not my_loc.latitude or not my_loc.longitude:
        return []

    connection_ids = _get_connection_ids(user)

    qs = UserLocation.objects.exclude(user=user).select_related(
        'user', 'user__fitness_profile', 'user__creator_profile'
    ).filter(
        latitude__isnull=False, longitude__isnull=False
    ).exclude(visibility='hidden')

    # Honour visibility: 'connections' only visible to connected users
    qs = qs.filter(
        Q(visibility='public') |
        Q(visibility='connections', user_id__in=connection_ids)
    )

    qs = filter_qs_by_radius(qs, float(my_loc.latitude), float(my_loc.longitude), radius_km)

    people = attach_distance(
        list(qs),
        float(my_loc.latitude), float(my_loc.longitude),
        radius_km=radius_km,
    )

    # Attach connection status to each
    pending_sent = set(
        ConnectionRequest.objects.filter(
            sender=user, status='pending'
        ).values_list('receiver_id', flat=True)
    )
    pending_received = set(
        ConnectionRequest.objects.filter(
            receiver=user, status='pending'
        ).values_list('sender_id', flat=True)
    )

    for loc in people:
        uid = loc.user_id
        if uid in connection_ids:
            loc.connection_status = 'connected'
        elif uid in pending_sent:
            loc.connection_status = 'request_sent'
        elif uid in pending_received:
            loc.connection_status = 'request_received'
        else:
            loc.connection_status = 'none'

    return people


# ── Connection requests ────────────────────────────────────────────────────────

def send_connection_request(sender, receiver, message: str = '') -> ConnectionRequest:
    if sender == receiver:
        raise ValueError("Cannot send a connection request to yourself.")

    if _are_connected(sender, receiver):
        raise ValueError("You are already connected.")

    existing = ConnectionRequest.objects.filter(
        Q(sender=sender, receiver=receiver) |
        Q(sender=receiver, receiver=sender)
    ).filter(status='pending').first()

    if existing:
        raise ValueError("A pending request already exists between these users.")

    return ConnectionRequest.objects.create(
        sender=sender, receiver=receiver, message=message[:300]
    )


def respond_to_request(request: ConnectionRequest, receiver, accept: bool) -> dict:
    if request.receiver != receiver:
        raise PermissionError("Not authorised to respond to this request.")
    if request.status != 'pending':
        raise ValueError("Request is no longer pending.")

    request.responded_at = timezone.now()
    if accept:
        request.status = 'accepted'
        request.save()
        conn = UserConnection.objects.create(user1=request.sender, user2=request.receiver)
        return {'accepted': True, 'connection': conn}
    else:
        request.status = 'rejected'
        request.save()
        return {'accepted': False, 'connection': None}


def withdraw_request(request: ConnectionRequest, sender) -> None:
    if request.sender != sender:
        raise PermissionError("Not authorised.")
    if request.status != 'pending':
        raise ValueError("Request is no longer pending.")
    request.status = 'withdrawn'
    request.save()


def remove_connection(user, other_user) -> None:
    conn = UserConnection.objects.filter(
        Q(user1=user, user2=other_user) | Q(user1=other_user, user2=user)
    ).first()
    if not conn:
        raise ValueError("No connection exists.")
    conn.delete()


# ── Queries ────────────────────────────────────────────────────────────────────

def get_connections(user) -> QuerySet:
    ids = _get_connection_ids(user)
    from django.contrib.auth.models import User
    return User.objects.filter(id__in=ids).select_related('location', 'fitness_profile')


def get_pending_received(user) -> QuerySet:
    return ConnectionRequest.objects.filter(
        receiver=user, status='pending'
    ).select_related('sender', 'sender__location', 'sender__fitness_profile')


def get_pending_sent(user) -> QuerySet:
    return ConnectionRequest.objects.filter(
        sender=user, status='pending'
    ).select_related('receiver', 'receiver__location')


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_connection_ids(user) -> set:
    from_user1 = UserConnection.objects.filter(user1=user).values_list('user2_id', flat=True)
    from_user2 = UserConnection.objects.filter(user2=user).values_list('user1_id', flat=True)
    return set(from_user1) | set(from_user2)


def _are_connected(user1, user2) -> bool:
    return UserConnection.objects.filter(
        Q(user1=user1, user2=user2) | Q(user1=user2, user2=user1)
    ).exists()
