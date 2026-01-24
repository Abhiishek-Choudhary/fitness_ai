from django.db import models
from django.conf import settings

class Workout(models.Model):
    WORKOUT_TYPE_CHOICES = [
        ('cardio', 'Cardio'),
        ('strength', 'Strength'),
        ('flexibility', 'Flexibility'),
        ('hiit', 'HIIT'),
        ('yoga', 'Yoga'),
    ]

    name = models.CharField(max_length=100)
    workout_type = models.CharField(max_length=20, choices=WORKOUT_TYPE_CHOICES)
    met = models.FloatField(help_text="Metabolic Equivalent of Task")

    def __str__(self):
        return f"{self.name} ({self.workout_type})"


class WorkoutSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='workout_sessions'
    )
    workout = models.ForeignKey(Workout, on_delete=models.CASCADE)
    duration_minutes = models.PositiveIntegerField()
    calories_burned = models.FloatField(null=True, blank=True)
    date = models.DateField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate calories burned on save
        try:
            weight = self.user.fitness_profile.weight_kg
        except:
            weight = 70  # default weight if not available
        duration_hours = self.duration_minutes / 60
        self.calories_burned = round(self.workout.met * weight * duration_hours, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.workout.name} ({self.date})"
