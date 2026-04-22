from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ContentPost, PostComment, CreatorProfile, Tag, UserFollow


# ── Reusable sub-serializers ──────────────────────────────────────────────────

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']


class CreatorSummarySerializer(serializers.ModelSerializer):
    """Minimal creator info embedded in post cards."""
    name = serializers.SerializerMethodField()
    avatar_url = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    specialization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'name', 'avatar_url', 'is_verified', 'specialization']

    def get_name(self, obj):
        return obj.get_full_name() or obj.username

    def _profile(self, obj):
        return getattr(obj, 'creator_profile', None)

    def get_avatar_url(self, obj):
        p = self._profile(obj)
        return p.avatar_url if p else ''

    def get_is_verified(self, obj):
        p = self._profile(obj)
        return p.is_verified if p else False

    def get_specialization(self, obj):
        p = self._profile(obj)
        return p.specialization if p else ''


class CreatorProfileSerializer(serializers.ModelSerializer):
    user = CreatorSummarySerializer(read_only=True)
    followers_count = serializers.ReadOnlyField()
    posts_count = serializers.ReadOnlyField()

    class Meta:
        model = CreatorProfile
        fields = [
            'user', 'bio', 'avatar_url', 'is_verified', 'specialization',
            'website', 'instagram_handle', 'followers_count', 'posts_count',
        ]


# ── Post serializers ──────────────────────────────────────────────────────────

class PostCardSerializer(serializers.ModelSerializer):
    """Lightweight card for feed lists — no heavy body text."""
    creator = CreatorSummarySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    embed_url = serializers.ReadOnlyField()
    user_liked = serializers.BooleanField(read_only=True, default=False)
    user_saved = serializers.BooleanField(read_only=True, default=False)
    duration_label = serializers.SerializerMethodField()

    class Meta:
        model = ContentPost
        fields = [
            'id', 'creator', 'title', 'content_type', 'fitness_category', 'difficulty',
            'thumbnail_url', 'youtube_video_id', 'embed_url', 'video_url', 'duration_label',
            'tags', 'likes_count', 'comments_count', 'views_count',
            'user_liked', 'user_saved', 'is_featured', 'created_at',
        ]

    def get_duration_label(self, obj):
        if not obj.duration_seconds:
            return None
        m, s = divmod(obj.duration_seconds, 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


class PostDetailSerializer(PostCardSerializer):
    """Full post detail including body text and nested comments."""
    class Meta(PostCardSerializer.Meta):
        fields = PostCardSerializer.Meta.fields + ['body', 'source', 'updated_at']


class PostCreateSerializer(serializers.ModelSerializer):
    tag_names = serializers.ListField(
        child=serializers.CharField(max_length=50), write_only=True, required=False, default=list
    )

    class Meta:
        model = ContentPost
        fields = [
            'title', 'body', 'content_type', 'fitness_category', 'difficulty',
            'thumbnail_url', 'video_url', 'youtube_video_id',
            'duration_seconds', 'tag_names', 'status',
        ]

    def create(self, validated_data):
        tag_names = validated_data.pop('tag_names', [])
        post = ContentPost.objects.create(**validated_data)
        tags = [Tag.objects.get_or_create(name=n.lower())[0] for n in tag_names]
        post.tags.set(tags)
        return post

    def update(self, instance, validated_data):
        tag_names = validated_data.pop('tag_names', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if tag_names is not None:
            tags = [Tag.objects.get_or_create(name=n.lower())[0] for n in tag_names]
            instance.tags.set(tags)
        return instance


# ── Comment serializers ───────────────────────────────────────────────────────

class CommentReplySerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = PostComment
        fields = ['id', 'author', 'body', 'created_at']

    def get_author(self, obj):
        return CreatorSummarySerializer(obj.user).data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    replies = CommentReplySerializer(many=True, read_only=True)

    class Meta:
        model = PostComment
        fields = ['id', 'author', 'body', 'parent', 'replies', 'created_at', 'updated_at']
        read_only_fields = ['author', 'replies', 'created_at', 'updated_at']

    def get_author(self, obj):
        return CreatorSummarySerializer(obj.user).data


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostComment
        fields = ['body', 'parent']

    def validate_parent(self, parent):
        if parent and parent.parent_id is not None:
            raise serializers.ValidationError("Nested replies beyond one level are not allowed.")
        return parent


# ── Follow / action serializers ───────────────────────────────────────────────

class FollowSerializer(serializers.ModelSerializer):
    follower = CreatorSummarySerializer(read_only=True)
    following = CreatorSummarySerializer(read_only=True)

    class Meta:
        model = UserFollow
        fields = ['follower', 'following', 'created_at']
