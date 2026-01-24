from django.db import models
from django.conf import settings

class ProgressEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress_entries"
    )

    recorded_on = models.DateField(
        help_text="Date of the progress entry"
    )

    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Weight in kg"
    )

    note = models.TextField(
        blank=True,
        help_text="User notes about progress"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-recorded_on"]
        unique_together = ("user", "recorded_on")
        indexes = [
            models.Index(fields=["user", "recorded_on"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.recorded_on}"


class ProgressImage(models.Model):
    IMAGE_TYPES = (
        ("front", "Front"),
        ("side", "Side"),
        ("back", "Back"),
        ("other", "Other"),
    )

    entry = models.ForeignKey(
        ProgressEntry,
        on_delete=models.CASCADE,
        related_name="images"
    )

    image = models.ImageField(
        upload_to="progress_images/%Y/%m/%d/"
    )

    image_type = models.CharField(
        max_length=10,
        choices=IMAGE_TYPES,
        default="other"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image ({self.image_type}) - {self.entry}"
