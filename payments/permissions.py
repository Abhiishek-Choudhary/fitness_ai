from django.utils import timezone
from rest_framework.permissions import BasePermission
from .models import UserSubscription


def get_active_subscription(user):
    """Return the user's current active, valid subscription or None."""
    sub = (
        UserSubscription.objects
        .filter(user=user, status='active')
        .select_related('plan')
        .order_by('-created_at')
        .first()
    )
    if sub and sub.is_valid:
        return sub
    return None


def get_user_tier(user):
    """Return 'free', 'pro', or 'elite'."""
    sub = get_active_subscription(user)
    return sub.plan.tier if sub else 'free'


class IsProOrElite(BasePermission):
    """Allow access only to Pro or Elite subscribers."""
    message = 'This feature requires a Pro or Elite subscription.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_tier(request.user) in ('pro', 'elite')


class IsElite(BasePermission):
    """Allow access only to Elite subscribers."""
    message = 'This feature requires an Elite subscription.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_tier(request.user) == 'elite'
