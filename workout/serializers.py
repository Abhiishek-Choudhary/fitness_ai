from rest_framework import serializers
from .models import Workout, WorkoutSession

class WorkoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workout
        fields = ['id', 'name', 'workout_type', 'met']


class WorkoutSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkoutSession
        fields = ['id', 'user', 'workout', 'duration_minutes', 'calories_burned', 'date']
        read_only_fields = ['user', 'calories_burned', 'date']
