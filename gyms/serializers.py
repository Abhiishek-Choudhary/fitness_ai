from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Gym, GymMedia, GymMembership, GymMessage, GymEmailCampaign


class OwnerMiniSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'name']

    def get_name(self, obj):
        return obj.get_full_name() or obj.username


# ── Gym serializers ────────────────────────────────────────────────────────────

class GymMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymMedia
        fields = ['id', 'image', 'caption', 'uploaded_at']
        read_only_fields = ['uploaded_at']


class GymCardSerializer(serializers.ModelSerializer):
    """Minimal fields for list / nearby cards."""
    gym_type_display = serializers.CharField(source='get_gym_type_display', read_only=True)
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = Gym
        fields = [
            'id', 'name', 'gym_type', 'gym_type_display',
            'city', 'state', 'country',
            'logo', 'cover_image',
            'monthly_fee', 'followers_count',
            'is_verified', 'is_active',
            'distance_km',
        ]

    def get_distance_km(self, obj):
        return getattr(obj, 'distance_km', None)


class GymDetailSerializer(serializers.ModelSerializer):
    """Full gym profile — used for GET /gyms/<id>/."""
    owner = OwnerMiniSerializer(read_only=True)
    media = GymMediaSerializer(many=True, read_only=True)
    gym_type_display = serializers.CharField(source='get_gym_type_display', read_only=True)
    is_following = serializers.SerializerMethodField()
    membership_status = serializers.SerializerMethodField()

    class Meta:
        model = Gym
        fields = [
            'id', 'owner',
            'name', 'gym_type', 'gym_type_display', 'description',
            'address', 'city', 'state', 'country', 'latitude', 'longitude',
            'phone', 'email', 'website',
            'amenities', 'opening_hours', 'monthly_fee',
            'logo', 'cover_image', 'media',
            'is_verified', 'is_active', 'followers_count',
            'is_following', 'membership_status',
            'created_at', 'updated_at',
        ]

    def get_is_following(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return GymMembership.objects.filter(user=request.user, gym=obj).exists()

    def get_membership_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        try:
            return GymMembership.objects.get(user=request.user, gym=obj).status
        except GymMembership.DoesNotExist:
            return None


class GymCreateUpdateSerializer(serializers.ModelSerializer):
    """Used for POST (register) and PUT/PATCH (update)."""

    class Meta:
        model = Gym
        fields = [
            'name', 'gym_type', 'description',
            'address', 'city', 'state', 'country', 'latitude', 'longitude',
            'phone', 'email', 'website',
            'amenities', 'opening_hours', 'monthly_fee',
            'logo', 'cover_image',
        ]

    def validate_amenities(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("amenities must be a list of strings.")
        return value

    def validate_opening_hours(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("opening_hours must be a dict.")
        return value


# ── Membership serializers ─────────────────────────────────────────────────────

class GymMembershipSerializer(serializers.ModelSerializer):
    user = OwnerMiniSerializer(read_only=True)
    gym_name = serializers.CharField(source='gym.name', read_only=True)

    class Meta:
        model = GymMembership
        fields = ['id', 'user', 'gym', 'gym_name', 'status', 'joined_at']
        read_only_fields = ['joined_at']


# ── Message serializers ────────────────────────────────────────────────────────

class GymMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = GymMessage
        fields = ['id', 'content', 'sender_name', 'is_from_owner', 'is_read', 'created_at']
        read_only_fields = ['sender_name', 'is_from_owner', 'is_read', 'created_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username


class GymMessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(min_length=1, max_length=2000)


class ConversationThreadSerializer(serializers.Serializer):
    """Summary of one conversation in the owner's inbox."""
    user = OwnerMiniSerializer()
    last_message = serializers.CharField()
    last_message_at = serializers.DateTimeField()
    unread_count = serializers.IntegerField()


# ── Campaign serializers ───────────────────────────────────────────────────────

class GymCampaignCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GymEmailCampaign
        fields = ['subject', 'body', 'campaign_type', 'target_radius_km']

    def validate_target_radius_km(self, value):
        if value <= 0 or value > 200:
            raise serializers.ValidationError("Radius must be between 1 and 200 km.")
        return value


class GymCampaignListSerializer(serializers.ModelSerializer):
    gym_name = serializers.CharField(source='gym.name', read_only=True)
    gym_logo = serializers.ImageField(source='gym.logo', read_only=True)
    campaign_type_display = serializers.CharField(
        source='get_campaign_type_display', read_only=True
    )

    class Meta:
        model = GymEmailCampaign
        fields = [
            'id', 'gym', 'gym_name', 'gym_logo',
            'subject', 'body', 'campaign_type', 'campaign_type_display',
            'target_radius_km', 'sent_at', 'sent_to_count', 'created_at',
        ]
