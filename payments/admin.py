from django.contrib import admin
from .models import Plan, RazorpayOrder, Payment, UserSubscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'billing_cycle', 'price_inr', 'is_active', 'is_popular']
    list_editable = ['is_active', 'is_popular']
    list_filter = ['tier', 'billing_cycle', 'is_active']


@admin.register(RazorpayOrder)
class RazorpayOrderAdmin(admin.ModelAdmin):
    list_display = ['razorpay_order_id', 'user', 'plan', 'amount_paise', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['razorpay_order_id', 'user__email']
    readonly_fields = ['razorpay_order_id', 'receipt', 'created_at', 'updated_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['razorpay_payment_id', 'user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['razorpay_payment_id', 'user__email']
    readonly_fields = ['razorpay_payment_id', 'razorpay_signature', 'created_at']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'starts_at', 'expires_at', 'is_valid']
    list_filter = ['status', 'plan__tier']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']
