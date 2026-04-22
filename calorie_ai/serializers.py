from rest_framework import serializers
from .models import FoodLog


class FoodImageSerializer(serializers.Serializer):
    image = serializers.ImageField()


class FoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodLog
        fields = [
            'id', 'food_name', 'meal_type', 'calories',
            'protein_g', 'carbs_g', 'fat_g',
            'quantity_description', 'logged_on', 'created_at',
        ]
        read_only_fields = ['created_at']


class FoodLogCreateFromEstimateSerializer(serializers.Serializer):
    """Log multiple food items returned from the estimate endpoint in one shot."""
    items = serializers.ListField(
        child=serializers.DictField(),
        help_text="List of {name, calories, quantity} dicts from /api/calories/estimate/"
    )
    meal_type = serializers.ChoiceField(choices=['breakfast', 'lunch', 'dinner', 'snack'])
    logged_on = serializers.DateField()
