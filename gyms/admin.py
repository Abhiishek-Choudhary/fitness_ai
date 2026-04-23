from django.contrib import admin
from .models import Gym, GymMedia, GymMembership, GymMessage, GymEmailCampaign


class GymMediaInline(admin.TabularInline):
    model = GymMedia
    extra = 0
    readonly_fields = ['uploaded_at']


@admin.register(Gym)
class GymAdmin(admin.ModelAdmin):
    list_display = ['name', 'gym_type', 'city', 'owner', 'is_verified', 'is_active', 'followers_count']
    list_filter = ['gym_type', 'city', 'is_verified', 'is_active']
    search_fields = ['name', 'city', 'owner__email']
    readonly_fields = ['followers_count', 'created_at', 'updated_at']
    inlines = [GymMediaInline]
    actions = ['verify_gyms', 'deactivate_gyms']

    @admin.action(description='Mark selected gyms as verified')
    def verify_gyms(self, request, queryset):
        queryset.update(is_verified=True)

    @admin.action(description='Deactivate selected gyms')
    def deactivate_gyms(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(GymMembership)
class GymMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'gym', 'status', 'joined_at']
    list_filter = ['status']
    search_fields = ['user__email', 'gym__name']


@admin.register(GymMessage)
class GymMessageAdmin(admin.ModelAdmin):
    list_display = ['gym', 'conversation_user', 'sender', 'is_from_owner', 'is_read', 'created_at']
    list_filter = ['is_from_owner', 'is_read']
    search_fields = ['gym__name', 'sender__email']


@admin.register(GymEmailCampaign)
class GymEmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['gym', 'subject', 'campaign_type', 'sent_at', 'sent_to_count']
    list_filter = ['campaign_type']
    search_fields = ['gym__name', 'subject']
    readonly_fields = ['sent_at', 'sent_to_count']
