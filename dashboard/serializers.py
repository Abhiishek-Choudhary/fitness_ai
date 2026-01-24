from rest_framework import serializers
from .models import ProgressEntry, ProgressImage
from datetime import date

# Serializer for creating a single image (used in create API)
class ProgressImageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressImage
        fields = ["image", "image_type"]

# Serializer for listing images (read-only, used in list API)
class ProgressImageListSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProgressImage
        fields = ["id", "image_url", "image_type", "created_at"]

    def get_image_url(self, obj):
        request = self.context.get("request")
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return None

# Serializer for creating a progress entry (single image input)
class ProgressEntryCreateSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
    note = serializers.CharField(required=False, allow_blank=True)
    weight = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    recorded_on = serializers.DateField(required=False)

    def validate_recorded_on(self, value):
        if value and value > date.today():
            raise serializers.ValidationError("Future dates are not allowed.")
        return value

    def validate(self, attrs):
        # Default recorded_on to today if not provided
        if "recorded_on" not in attrs or not attrs["recorded_on"]:
            attrs["recorded_on"] = date.today()
        return attrs

# Serializer for listing progress entries
class ProgressEntryListSerializer(serializers.ModelSerializer):
    images = ProgressImageListSerializer(many=True, read_only=True)  # list of all images

    class Meta:
        model = ProgressEntry
        fields = (
            "id",
            "images",  # all associated images
            "note",
            "weight",
            "recorded_on",
            "created_at",
        )
