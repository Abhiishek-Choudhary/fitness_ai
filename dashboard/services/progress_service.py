from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Prefetch

from dashboard.models import ProgressEntry, ProgressImage


def _attach_images(*, entry, images_data):
    """
    Attach uploaded images to a progress entry.
    """
    images = []
    for image_data in images_data:
        images.append(
            ProgressImage(
                entry=entry,  # ✅ FIXED
                image=image_data["image"],
                image_type=image_data.get("image_type", "front"),
            )
        )
    ProgressImage.objects.bulk_create(images)


@transaction.atomic
def create_or_update_progress_entry(
    *,
    user,
    recorded_on,
    weight=None,
    note=None,
    images_data=None,
):
    """
    Creates or updates a progress entry for a given user and date.
    Enforces one entry per user per recorded_on date.
    """
    entry, created = ProgressEntry.objects.get_or_create(
        user=user,
        recorded_on=recorded_on,  # updated field
        defaults={
            "weight": weight,
            "note": note,
        },
    )

    # Update existing entry if already present
    if not created:
        update_fields = []
        if weight is not None and entry.weight != weight:
            entry.weight = weight
            update_fields.append("weight")
        if note is not None and entry.note != note:
            entry.note = note
            update_fields.append("note")

        if update_fields:
            entry.save(update_fields=update_fields)

    # Handle images (optional)
    if images_data:
        _attach_images(entry=entry, images_data=images_data)

    return entry


@transaction.atomic
def delete_progress_entry(*, user, entry_id):
    """
    Deletes a progress entry for the given user.
    Raises ValidationError if not found.
    """
    try:
        entry = ProgressEntry.objects.get(id=entry_id, user=user)
    except ProgressEntry.DoesNotExist:
        raise ValidationError("Progress entry not found")

    entry.delete()


def get_user_progress_entries(*, user):
    """
    Returns all progress entries for a user, newest first.
    Prefetches related images efficiently.
    """
    return (
        ProgressEntry.objects
        .filter(user=user)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProgressImage.objects.only("id", "image", "image_type")
            )
        )
        .order_by("-recorded_on")  # updated field
    )
