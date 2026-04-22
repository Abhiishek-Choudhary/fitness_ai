from django.contrib import admin
from .models import ContentPost, CreatorProfile, Tag, PostComment, PostLike, UserFollow, SavedPost


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'is_verified', 'followers_count', 'posts_count']
    list_editable = ['is_verified']
    search_fields = ['user__username', 'user__email', 'specialization']


@admin.register(ContentPost)
class ContentPostAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'creator', 'content_type', 'fitness_category',
        'difficulty', 'status', 'likes_count', 'views_count', 'is_featured', 'created_at',
    ]
    list_filter = ['status', 'content_type', 'fitness_category', 'difficulty', 'source']
    list_editable = ['status', 'is_featured']
    search_fields = ['title', 'creator__username', 'youtube_video_id']
    readonly_fields = ['likes_count', 'views_count', 'comments_count', 'created_at', 'updated_at']
    filter_horizontal = ['tags']


@admin.register(PostComment)
class PostCommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'parent', 'created_at']
    search_fields = ['user__email', 'post__title']


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'created_at']


@admin.register(UserFollow)
class UserFollowAdmin(admin.ModelAdmin):
    list_display = ['follower', 'following', 'created_at']


@admin.register(SavedPost)
class SavedPostAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'saved_at']
