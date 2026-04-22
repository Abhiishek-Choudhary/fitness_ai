from django.db import models
from django.contrib.auth.models import User


# ── Shared constant tables ─────────────────────────────────────────────────────

ACTIVITY_CHOICES = [
    ('running',       'Running'),
    ('cycling',       'Cycling'),
    ('hiking',        'Hiking'),
    ('outdoor_yoga',  'Outdoor Yoga'),
    ('outdoor_hiit',  'Outdoor HIIT'),
    ('swimming',      'Swimming'),
    ('sports',        'Sports'),
    ('gym_meetup',    'Gym Meetup'),
    ('walking',       'Walking / Trekking'),
    ('martial_arts',  'Martial Arts'),
    ('crossfit',      'CrossFit'),
    ('other',         'Other'),
]

DIFFICULTY_CHOICES = [
    ('all',           'All Levels'),
    ('beginner',      'Beginner'),
    ('intermediate',  'Intermediate'),
    ('advanced',      'Advanced'),
]


# ── Location ───────────────────────────────────────────────────────────────────

class UserLocation(models.Model):
    VISIBILITY_CHOICES = [
        ('public',      'Public — anyone can discover me'),
        ('connections', 'Connections Only'),
        ('hidden',      'Hidden — do not show me in discovery'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='location')
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='connections')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} — {self.city}, {self.country}"


# ── Events ─────────────────────────────────────────────────────────────────────

class FitnessEvent(models.Model):
    STATUS_CHOICES = [
        ('upcoming',   'Upcoming'),
        ('ongoing',    'Ongoing'),
        ('completed',  'Completed'),
        ('cancelled',  'Cancelled'),
    ]
    PRIVACY_CHOICES = [
        ('public',       'Public'),
        ('invite_only',  'Invite Only'),
    ]

    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organised_events')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all')
    cover_image_url = models.URLField(blank=True)

    # Location
    venue_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Schedule
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)

    # Capacity
    max_participants = models.PositiveIntegerField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='public')

    # Denormalised for fast reads
    attendees_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['event_date', 'start_time']
        indexes = [
            models.Index(fields=['event_date', 'status']),
            models.Index(fields=['city', 'activity_type']),
            models.Index(fields=['latitude', 'longitude']),
        ]

    def __str__(self):
        return f"{self.title} ({self.event_date})"

    @property
    def is_full(self):
        return self.max_participants is not None and self.attendees_count >= self.max_participants

    @property
    def spots_left(self):
        if self.max_participants is None:
            return None
        return max(0, self.max_participants - self.attendees_count)


class EventAttendee(models.Model):
    RSVP_CHOICES = [
        ('going',      'Going'),
        ('maybe',      'Maybe'),
        ('not_going',  'Not Going'),
    ]

    event = models.ForeignKey(FitnessEvent, on_delete=models.CASCADE, related_name='attendees')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_rsvps')
    rsvp_status = models.CharField(max_length=20, choices=RSVP_CHOICES, default='going')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user.email} → {self.event.title} ({self.rsvp_status})"


# ── Groups ─────────────────────────────────────────────────────────────────────

class CommunityGroup(models.Model):
    PRIVACY_CHOICES = [
        ('public',  'Public — anyone can join'),
        ('private', 'Private — admin approval required'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    activity_focus = models.CharField(max_length=30, choices=ACTIVITY_CHOICES)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all')
    cover_image_url = models.URLField(blank=True)

    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')

    # Denormalised
    members_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-members_count']
        indexes = [models.Index(fields=['city', 'activity_focus'])]

    def __str__(self):
        return self.name


class GroupMember(models.Model):
    ROLE_CHOICES = [
        ('admin',  'Admin'),
        ('member', 'Member'),
    ]
    STATUS_CHOICES = [
        ('active',   'Active'),
        ('pending',  'Pending Approval'),
        ('banned',   'Banned'),
    ]

    group = models.ForeignKey(CommunityGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.email} in {self.group.name} ({self.role})"


# ── Connections ────────────────────────────────────────────────────────────────

class ConnectionRequest(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('accepted',  'Accepted'),
        ('rejected',  'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_connection_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_connection_requests')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.email} → {self.receiver.email} ({self.status})"


class UserConnection(models.Model):
    """Symmetric friendship / connection record."""
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_initiated')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='connections_received')
    connected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')
        ordering = ['-connected_at']

    def __str__(self):
        return f"{self.user1.email} ↔ {self.user2.email}"
