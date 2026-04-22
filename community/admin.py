from django.contrib import admin
from .models import (
    UserLocation, FitnessEvent, EventAttendee,
    CommunityGroup, GroupMember,
    ConnectionRequest, UserConnection,
)


@admin.register(UserLocation)
class UserLocationAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'state', 'country', 'visibility', 'updated_at']
    list_filter = ['visibility', 'country']
    search_fields = ['user__email', 'city', 'country']


@admin.register(FitnessEvent)
class FitnessEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'activity_type', 'city', 'event_date', 'status', 'attendees_count', 'privacy']
    list_filter = ['status', 'activity_type', 'privacy', 'difficulty']
    search_fields = ['title', 'organizer__email', 'city']
    readonly_fields = ['attendees_count', 'created_at', 'updated_at']
    date_hierarchy = 'event_date'


@admin.register(EventAttendee)
class EventAttendeeAdmin(admin.ModelAdmin):
    list_display = ['event', 'user', 'rsvp_status', 'joined_at']
    list_filter = ['rsvp_status']
    search_fields = ['event__title', 'user__email']


@admin.register(CommunityGroup)
class CommunityGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'activity_focus', 'city', 'privacy', 'members_count', 'created_at']
    list_filter = ['privacy', 'activity_focus']
    search_fields = ['name', 'creator__email', 'city']
    readonly_fields = ['members_count', 'created_at']


@admin.register(GroupMember)
class GroupMemberAdmin(admin.ModelAdmin):
    list_display = ['group', 'user', 'role', 'status', 'joined_at']
    list_filter = ['role', 'status']
    search_fields = ['group__name', 'user__email']


@admin.register(ConnectionRequest)
class ConnectionRequestAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['sender__email', 'receiver__email']


@admin.register(UserConnection)
class UserConnectionAdmin(admin.ModelAdmin):
    list_display = ['user1', 'user2', 'connected_at']
    search_fields = ['user1__email', 'user2__email']
