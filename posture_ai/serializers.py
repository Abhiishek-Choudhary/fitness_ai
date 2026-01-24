from rest_framework import serializers
from .models import PostureSession, PostureImage

class PostureImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostureImage
        fields = ["id", "image"]

class PostureSessionSerializer(serializers.ModelSerializer):
    images = PostureImageSerializer(many=True, read_only=True)

    class Meta:
        model = PostureSession
        fields = [
            "id",
            "exercise_type",
            "final_score",
            "is_correct",
            "feedback",
            "images",
            "created_at",
        ]
