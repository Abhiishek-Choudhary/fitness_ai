from rest_framework import serializers
from .models import Plan, RazorpayOrder, Payment, UserSubscription


class PlanSerializer(serializers.ModelSerializer):
    price_paise = serializers.ReadOnlyField()

    class Meta:
        model = Plan
        fields = [
            'id', 'name', 'tier', 'billing_cycle', 'price_inr', 'price_paise',
            'description', 'features', 'is_popular',
            'ai_plans_per_month', 'ai_regenerations_per_month',
            'posture_analyses_per_month', 'calorie_estimates_per_day',
            'workout_sessions_per_month',
        ]


class CreateOrderSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()

    def validate_plan_id(self, value):
        try:
            plan = Plan.objects.get(id=value, is_active=True)
        except Plan.DoesNotExist:
            raise serializers.ValidationError("Plan not found or inactive.")
        if plan.price_inr == 0:
            raise serializers.ValidationError("Free plan does not require payment.")
        return value


class VerifyPaymentSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()


class PaymentSerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='order.plan.name', read_only=True)
    amount_inr = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = ['id', 'razorpay_payment_id', 'status', 'plan_name', 'amount_inr', 'created_at']

    def get_amount_inr(self, obj):
        return obj.order.amount_paise / 100


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    is_valid = serializers.ReadOnlyField()

    class Meta:
        model = UserSubscription
        fields = ['id', 'plan', 'status', 'starts_at', 'expires_at', 'is_valid', 'created_at']


class PaymentHistorySerializer(serializers.ModelSerializer):
    plan_name = serializers.CharField(source='order.plan.name', read_only=True)
    billing_cycle = serializers.CharField(source='order.plan.billing_cycle', read_only=True)
    amount_inr = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'razorpay_payment_id', 'status',
            'plan_name', 'billing_cycle', 'amount_inr', 'created_at'
        ]

    def get_amount_inr(self, obj):
        return obj.order.amount_paise / 100
