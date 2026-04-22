from django.contrib.auth.models import User
from rest_framework import serializers

from .models import (
    UserLocation, FitnessEvent, EventAttendee,
    CommunityGroup, GroupMember,
    ConnectionRequest, UserConnection,
    ACTIVITY_CHOICES, DIFFICULTY_CHOICES,
)


# ── Reusable micro-serializers ─────────────────────────────────────────────────

class UserMiniSerializer(serializers.ModelSerializer):
    """Embedded user card: name + avatar + city + goal."""
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    fitness_goal = serializers.SerializerMethodField()
    fitness_level = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar_url', 'city', 'fitness_goal', 'fitness_level']

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar_url(self, obj):
        profile = getattr(obj, 'creator_profile', None)
        return profile.avatar_url if profile else ''

    def get_city(self, obj):
        loc = getattr(obj, 'location', None)
        return loc.city if loc else ''

    def get_fitness_goal(self, obj):
        fp = getattr(obj, 'fitness_profile', None)
        return fp.fitness_goal if fp else ''

    def get_fitness_level(self, obj):
        fp = getattr(obj, 'fitness_profile', None)
        return fp.fitness_level if fp else ''


# ── Location ───────────────────────────────────────────────────────────────────

class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['city', 'state', 'country', 'latitude', 'longitude', 'visibility', 'updated_at']
        read_only_fields = ['updated_at']

    def validate(self, data):
        lat = data.get('latitude')
        lon = data.get('longitude')
        if (lat is None) != (lon is None):
            raise serializers.ValidationError("Both latitude and longitude must be provided together.")
        return data


# ── Events ─────────────────────────────────────────────────────────────────────

class EventCardSerializer(serializers.ModelSerializer):
    organizer = UserMiniSerializer(read_only=True)
    is_full = serializers.ReadOnlyField()
    spots_left = serializers.ReadOnlyField()
    distance_km = serializers.FloatField(read_only=True, default=None)
    user_rsvp = serializers.SerializerMethodField()

    class Meta:
        model = FitnessEvent
        fields = [
            'id', 'organizer', 'title', 'activity_type', 'difficulty',
            'cover_image_url', 'venue_name', 'city', 'state', 'country',
            'event_date', 'start_time', 'end_time',
            'max_participants', 'attendees_count', 'is_full', 'spots_left',
            'status', 'privacy', 'distance_km', 'user_rsvp', 'created_at',
        ]

    def get_user_rsvp(self, obj):
        user = self.context.get('request', None)
        if user and hasattr(user, 'user') and user.user.is_authenticated:
            attendee = EventAttendee.objects.filter(event=obj, user=user.user).first()
            return attendee.rsvp_status if attendee else None
        return None


class EventDetailSerializer(EventCardSerializer):
    attendees = serializers.SerializerMethodField()

    class Meta(EventCardSerializer.Meta):
        fields = EventCardSerializer.Meta.fields + ['description', 'address', 'latitude', 'longitude', 'attendees', 'updated_at']

    def get_attendees(self, obj):
        going = EventAttendee.objects.filter(event=obj, rsvp_status='going').select_related('user')[:20]
        return UserMiniSerializer([a.user for a in going], many=True).data


class EventCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessEvent
        fields = [
            'title', 'description', 'activity_type', 'difficulty',
            'cover_image_url', 'venue_name', 'address',
            'city', 'state', 'country', 'latitude', 'longitude',
            'event_date', 'start_time', 'end_time',
            'max_participants', 'privacy',
        ]

    def validate_event_date(self, value):
        from datetime import date
        if value < date.today():
            raise serializers.ValidationError("Event date cannot be in the past.")
        return value


class RSVPSerializer(serializers.Serializer):
    rsvp_status = serializers.ChoiceField(choices=['going', 'maybe', 'not_going'], default='going')


# ── Groups ─────────────────────────────────────────────────────────────────────

class GroupCardSerializer(serializers.ModelSerializer):
    creator = UserMiniSerializer(read_only=True)
    membership_status = serializers.SerializerMethodField()

    class Meta:
        model = CommunityGroup
        fields = [
            'id', 'creator', 'name', 'activity_focus', 'difficulty',
            'cover_image_url', 'city', 'state', 'country',
            'privacy', 'members_count', 'membership_status', 'created_at',
        ]

    def get_membership_status(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        member = GroupMember.objects.filter(group=obj, user=request.user).first()
        return member.status if member else None


class GroupDetailSerializer(GroupCardSerializer):
    recent_members = serializers.SerializerMethodField()

    class Meta(GroupCardSerializer.Meta):
        fields = GroupCardSerializer.Meta.fields + ['description', 'recent_members', 'updated_at']

    def get_recent_members(self, obj):
        members = GroupMember.objects.filter(
            group=obj, status='active'
        ).select_related('user').order_by('joined_at')[:12]
        return UserMiniSerializer([m.user for m in members], many=True).data


class GroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityGroup
        fields = [
            'name', 'description', 'activity_focus', 'difficulty',
            'cover_image_url', 'city', 'state', 'country', 'privacy',
        ]


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)

    class Meta:
        model = GroupMember
        fields = ['id', 'user', 'role', 'status', 'joined_at']


# ── Connections ────────────────────────────────────────────────────────────────

class NearbyPersonSerializer(serializers.Serializer):
    """Serialises a UserLocation with attached distance_km and connection_status."""
    user = UserMiniSerializer(read_only=True)
    city = serializers.CharField()
    state = serializers.CharField()
    country = serializers.CharField()
    visibility = serializers.CharField()
    distance_km = serializers.FloatField(default=None)
    connection_status = serializers.CharField(default='none')


class ConnectionRequestSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    receiver = UserMiniSerializer(read_only=True)

    class Meta:
        model = ConnectionRequest
        fields = ['id', 'sender', 'receiver', 'status', 'message', 'created_at', 'responded_at']


class SendConnectionRequestSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    message = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def validate_receiver_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value


class RespondRequestSerializer(serializers.Serializer):
    accept = serializers.BooleanField()


class ConnectedUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    fitness_goal = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar_url', 'city', 'fitness_goal']

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_avatar_url(self, obj):
        p = getattr(obj, 'creator_profile', None)
        return p.avatar_url if p else ''

    def get_city(self, obj):
        loc = getattr(obj, 'location', None)
        return loc.city if loc else ''

    def get_fitness_goal(self, obj):
        fp = getattr(obj, 'fitness_profile', None)
        return fp.fitness_goal if fp else ''
