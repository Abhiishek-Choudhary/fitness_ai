from django.db import models


class PostureSession(models.Model):
    EXERCISE_CHOICES = (
        ('push_up', 'Push Up'),
    )

    exercise_type = models.CharField(max_length=50, choices=EXERCISE_CHOICES)
    final_score = models.FloatField(null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    # AI feedback like:
    # { "back": "too arched", "elbow": "too wide" }
    feedback = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exercise_type} | {self.final_score}"


class PostureImage(models.Model):
    session = models.ForeignKey(
        PostureSession,
        related_name="images",
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="posture_images/")
    image_score = models.FloatField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"Image for session {self.session.id}"
