from django.db import models
from django.contrib.auth.models import User


class FoodLog(models.Model):
    MEAL_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('snack', 'Snack'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    food_name = models.CharField(max_length=200)
    meal_type = models.CharField(max_length=20, choices=MEAL_CHOICES, default='snack')
    calories = models.FloatField()
    protein_g = models.FloatField(default=0)
    carbs_g = models.FloatField(default=0)
    fat_g = models.FloatField(default=0)
    quantity_description = models.CharField(max_length=100, blank=True)
    logged_on = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_on', '-created_at']
        indexes = [models.Index(fields=['user', 'logged_on'])]

    def __str__(self):
        return f"{self.user.email} — {self.food_name} ({self.logged_on})"
