from rest_framework import serializers

class FoodImageSerializer(serializers.Serializer):
    image = serializers.ImageField()
