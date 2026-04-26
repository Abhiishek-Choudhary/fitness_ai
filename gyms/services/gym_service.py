"""
Gym service — Single Responsibility: business logic for gym CRUD,
nearby discovery, and membership management.
"""
from django.db import models as db_models, transaction

from community.services.geo_service import filter_qs_by_radius, attach_distance
from gyms.models import Gym, GymMembership


def get_nearby_gyms(lat: float, lon: float, radius_km: float = 10,
                    gym_type: str = None, city: str = None) -> list:
    """
    Return Gym objects within radius_km, sorted by distance ascending.
    Each object gets a `.distance_km` float attribute attached.
    Falls back to city/type filters when lat/lon are absent.
    """
    qs = Gym.objects.filter(is_active=True).select_related('owner')

    if gym_type:
        qs = qs.filter(gym_type=gym_type)
    if city:
        qs = qs.filter(city__icontains=city)

    if lat is not None and lon is not None:
        qs = filter_qs_by_radius(qs, lat, lon, radius_km)
        return attach_distance(list(qs), lat, lon, radius_km=radius_km)

    return list(qs)


def get_gyms_by_city(city: str, gym_type: str = None) -> list:
    qs = Gym.objects.filter(is_active=True, city__icontains=city).select_related('owner')
    if gym_type:
        qs = qs.filter(gym_type=gym_type)
    return list(qs)


@transaction.atomic
def toggle_follow(user, gym) -> tuple:
    """
    Follow the gym if not already following; unfollow if following.
    Returns (membership_or_None, created: bool).
    membership=None means the user unfollowed.
    """
    # select_for_update prevents race condition when two requests arrive simultaneously
    membership = (
        GymMembership.objects
        .select_for_update()
        .filter(user=user, gym=gym)
        .first()
    )
    if membership is not None:
        membership.delete()
        Gym.objects.filter(pk=gym.pk, followers_count__gt=0).update(
            followers_count=db_models.F('followers_count') - 1
        )
        return None, False
    else:
        membership = GymMembership.objects.create(user=user, gym=gym, status='following')
        Gym.objects.filter(pk=gym.pk).update(
            followers_count=db_models.F('followers_count') + 1
        )
        return membership, True


@transaction.atomic
def upgrade_to_member(gym, user):
    """Gym owner upgrades a follower's status to 'member'."""
    membership = GymMembership.objects.get(user=user, gym=gym)
    if membership.status != 'member':
        membership.status = 'member'
        membership.save(update_fields=['status'])
    return membership
