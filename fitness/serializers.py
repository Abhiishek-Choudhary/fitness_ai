from rest_framework import serializers
from .models import FitnessProfile


class FitnessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessProfile
        fields = [
            'age',
            'gender',
            'height_cm',
            'weight_kg',
            'fitness_goal',
            'fitness_level',
        ]

    def validate_age(self, value):
        if value < 13:
            raise serializers.ValidationError("Age must be at least 13")
        return value

    def validate_height_cm(self, value):
        if value <= 0:
            raise serializers.ValidationError("Height must be positive")
        return value

    def validate_weight_kg(self, value):
        if value <= 0:
            raise serializers.ValidationError("Weight must be positive")
        return value

class PromptSerializer(serializers.Serializer):
    prompt = serializers.CharField()

class FitnessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessProfile
        fields = [
            'age',
            'gender',
            'height_cm',
            'weight_kg',
            'fitness_goal',
            'fitness_level',
            'activity_level',  # NEW
        ]
