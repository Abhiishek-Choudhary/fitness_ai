from django.db import models
from django.contrib.auth.models import User


GYM_TYPE_CHOICES = [
    ('crossfit',      'CrossFit'),
    ('bodybuilding',  'Bodybuilding'),
    ('boxing',        'Boxing'),
    ('mma',           'MMA / Martial Arts'),
    ('yoga',          'Yoga'),
    ('pilates',       'Pilates'),
    ('general',       'General Fitness'),
    ('zumba',         'Zumba / Dance Fitness'),
    ('calisthenics',  'Calisthenics'),
    ('powerlifting',  'Powerlifting'),
    ('swimming',      'Swimming'),
    ('cycling',       'Cycling / Spinning'),
    ('functional',    'Functional Training'),
    ('kickboxing',    'Kickboxing'),
]


class Gym(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_gyms')
    name = models.CharField(max_length=200)
    gym_type = models.CharField(max_length=20, choices=GYM_TYPE_CHOICES)
    description = models.TextField(blank=True)

    # Location
    address = models.CharField(max_length=300)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='India')
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Contact
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    # Details — amenities is a JSON list e.g. ["WiFi", "Parking", "Sauna"]
    amenities = models.JSONField(default=list)
    # opening_hours format: {"mon": {"open": "06:00", "close": "22:00"}, "tue": {...}, ...}
    opening_hours = models.JSONField(default=dict)
    monthly_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    # Media
    logo = models.ImageField(upload_to='gym_logos/', null=True, blank=True)
    cover_image = models.ImageField(upload_to='gym_covers/', null=True, blank=True)

    # Status
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    followers_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'gym_type']),
            models.Index(fields=['latitude', 'longitude']),
            models.Index(fields=['owner']),
            models.Index(fields=['is_active', 'city']),
        ]

    def __str__(self):
        return f"{self.name} ({self.city})"


class GymMedia(models.Model):
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='media')
    image = models.ImageField(upload_to='gym_media/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.gym.name} — media {self.pk}"


class GymMembership(models.Model):
    STATUS_CHOICES = [
        ('following', 'Following'),
        ('member',    'Member'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gym_memberships')
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='memberships')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='following')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'gym')
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.gym.name} ({self.status})"


class GymMessage(models.Model):
    """
    One message in a (gym, user) conversation thread.
    conversation_user is always the non-owner participant so the gym owner
    can query all threads with .filter(gym=gym).
    """
    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='messages')
    conversation_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='gym_conversations'
    )
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gym_messages_sent')
    content = models.TextField()
    is_from_owner = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['gym', 'conversation_user', 'created_at']),
        ]

    def __str__(self):
        direction = 'owner→user' if self.is_from_owner else 'user→owner'
        return f"[{self.gym.name}] {direction} at {self.created_at:%Y-%m-%d %H:%M}"


class GymEmailCampaign(models.Model):
    CAMPAIGN_TYPE_CHOICES = [
        ('welcome',      'Welcome'),
        ('discount',     'Discount Offer'),
        ('announcement', 'Announcement'),
        ('event',        'Event Promotion'),
        ('newsletter',   'Newsletter'),
    ]

    gym = models.ForeignKey(Gym, on_delete=models.CASCADE, related_name='campaigns')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    campaign_type = models.CharField(max_length=20, choices=CAMPAIGN_TYPE_CHOICES)
    target_radius_km = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_to_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.gym.name}] {self.subject}"
