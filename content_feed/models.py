from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count


# ── Lookup / taxonomy ──────────────────────────────────────────────────────────

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)

    def __str__(self):
        return self.name


# ── Creator profile (extends User, one-to-one) ────────────────────────────────

class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    bio = models.TextField(blank=True)
    avatar_url = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)   # blue-tick
    specialization = models.CharField(max_length=100, blank=True)  # "Strength Coach", "Nutritionist" …
    website = models.URLField(blank=True)
    instagram_handle = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return f"@{self.user.username}"

    @property
    def followers_count(self):
        return UserFollow.objects.filter(following=self.user).count()

    @property
    def posts_count(self):
        return ContentPost.objects.filter(creator=self.user, status='published').count()


# ── Main content post ─────────────────────────────────────────────────────────

class ContentPost(models.Model):
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('article', 'Article'),
        ('exercise_guide', 'Exercise Guide'),
        ('nutrition_tip', 'Nutrition Tip'),
        ('transformation', 'Transformation'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    FITNESS_CATEGORY_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('cardio', 'Cardio'),
        ('strength', 'Strength'),
        ('yoga', 'Yoga'),
        ('hiit', 'HIIT'),
        ('nutrition', 'Nutrition'),
        ('flexibility', 'Flexibility'),
        ('general', 'General Fitness'),
    ]
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='content_posts')
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES, default='video')
    fitness_category = models.CharField(max_length=20, choices=FITNESS_CATEGORY_CHOICES, default='general')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')

    # Media
    thumbnail_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True)
    youtube_video_id = models.CharField(max_length=30, blank=True, db_index=True)

    # Taxonomy
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')

    # Meta
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='published')
    is_featured = models.BooleanField(default=False)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)  # video length
    source = models.CharField(max_length=50, default='user', blank=True)  # 'user' | 'youtube_seed'

    # Denormalized counters (updated via signals / service layer)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    comments_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'fitness_category']),
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['-likes_count']),
        ]

    def __str__(self):
        return f"[{self.content_type}] {self.title}"

    @property
    def embed_url(self):
        if self.youtube_video_id:
            return f"https://www.youtube.com/embed/{self.youtube_video_id}"
        return self.video_url


# ── Social interactions ───────────────────────────────────────────────────────

class PostLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.email} liked '{self.post.title}'"


class PostComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_comments')
    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.email} on '{self.post.title}'"


class UserFollow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.email} → {self.following.email}"


class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name='saves')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f"{self.user.email} saved '{self.post.title}'"


class PostView(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    post = models.ForeignKey(ContentPost, on_delete=models.CASCADE, related_name='post_views')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['post', 'viewed_at'])]
