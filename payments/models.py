from django.db import models
from django.contrib.auth.models import User


class Plan(models.Model):
    BILLING_CYCLE_CHOICES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('lifetime', 'Lifetime'),
    ]
    TIER_CHOICES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('elite', 'Elite'),
    ]

    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, default='free')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES, default='monthly')
    price_inr = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    features = models.JSONField(default=list)  # list of feature strings
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)

    # Limits
    ai_plans_per_month = models.IntegerField(default=1)       # -1 = unlimited
    ai_regenerations_per_month = models.IntegerField(default=0)
    posture_analyses_per_month = models.IntegerField(default=0)
    calorie_estimates_per_day = models.IntegerField(default=5)
    workout_sessions_per_month = models.IntegerField(default=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('tier', 'billing_cycle')
        ordering = ['price_inr']

    def __str__(self):
        return f"{self.name} ({self.billing_cycle})"

    @property
    def price_paise(self):
        """Razorpay uses paise (1 INR = 100 paise)."""
        return int(self.price_inr * 100)


class RazorpayOrder(models.Model):
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('attempted', 'Attempted'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='razorpay_orders')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    amount_paise = models.IntegerField()
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    receipt = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.razorpay_order_id} — {self.user.email}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ('captured', 'Captured'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    order = models.OneToOneField(RazorpayOrder, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    razorpay_payment_id = models.CharField(max_length=100, unique=True)
    razorpay_signature = models.CharField(max_length=256)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='captured')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment {self.razorpay_payment_id} — {self.user.email}"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField(null=True, blank=True)  # null = lifetime
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.plan.name} ({self.status})"

    @property
    def is_valid(self):
        from django.utils import timezone
        if self.status != 'active':
            return False
        if self.expires_at is None:
            return True
        return self.expires_at > timezone.now()
