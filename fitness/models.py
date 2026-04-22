from django.db import models
from django.contrib.auth.models import User


class FitnessProfile(models.Model):

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    FITNESS_GOAL_CHOICES = [
        ('WEIGHT_LOSS', 'Weight Loss'),
        ('MUSCLE_GAIN', 'Muscle Gain'),
        ('ENDURANCE', 'Endurance'),
        ('GENERAL_FITNESS', 'General Fitness'),
    ]

    FITNESS_LEVEL_CHOICES = [
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    ]
    
    ACTIVITY_LEVEL_CHOICES = [
        ('sedentary', 'Sedentary'),
        ('light', 'Light'),
        ('moderate', 'Moderate'),
        ('heavy', 'Heavy'),
        ('athlete', 'Athlete'),
    ]

    activity_level = models.CharField(
        max_length=20,
        choices=ACTIVITY_LEVEL_CHOICES,
        default='moderate'  # default for safety
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='fitness_profile'
    )

    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)

    height_cm = models.FloatField()
    weight_kg = models.FloatField()

    fitness_goal = models.CharField(
        max_length=20,
        choices=FITNESS_GOAL_CHOICES
    )

    fitness_level = models.CharField(
        max_length=20,
        choices=FITNESS_LEVEL_CHOICES
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} ({self.user.id})"

class UserPrompt(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="prompts"
    )
    prompt_text = models.TextField()

    primary_goal = models.CharField(max_length=50, blank=True)
    secondary_goal = models.CharField(max_length=50, blank=True)
    duration_weeks = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prompt by {self.user.username}"


class FitnessAIPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plan_json = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_plan(self, data: dict):
        self.plan_json = data

    def get_plan(self):
        return self.plan_json
