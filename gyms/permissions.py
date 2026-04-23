from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsGymOwnerOrReadOnly(BasePermission):
    """Allow any read; restrict writes to the gym's owner."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user


class IsGymOwner(BasePermission):
    """Allow only the gym's owner — no read exception."""

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
