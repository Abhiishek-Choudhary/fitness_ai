"""
Feed service — Single Responsibility: build feed querysets.
All DB access for the feed goes through here.
"""
from django.db.models import QuerySet, Exists, OuterRef, BooleanField, ExpressionWrapper
from content_feed.models import ContentPost, PostLike, SavedPost, UserFollow
from .recommendation import rank_feed_queryset, get_followed_creator_ids


def _base_published() -> QuerySet:
    return ContentPost.objects.filter(status='published').select_related(
        'creator', 'creator__creator_profile'
    ).prefetch_related('tags')


def _annotate_user_context(qs: QuerySet, user) -> QuerySet:
    """Annotate each post with whether the authenticated user liked/saved it."""
    if not user or not user.is_authenticated:
        return qs
    return qs.annotate(
        user_liked=Exists(
            PostLike.objects.filter(user=user, post=OuterRef('pk'))
        ),
        user_saved=Exists(
            SavedPost.objects.filter(user=user, post=OuterRef('pk'))
        ),
    )


def get_personalized_feed(user, category: str = None, content_type: str = None,
                           search: str = None) -> QuerySet:
    qs = _base_published()

    if category:
        qs = qs.filter(fitness_category=category)
    if content_type:
        qs = qs.filter(content_type=content_type)
    if search:
        qs = qs.filter(title__icontains=search) | qs.filter(body__icontains=search)

    if user and user.is_authenticated:
        qs = rank_feed_queryset(qs, user)
        qs = _annotate_user_context(qs, user)
    else:
        qs = qs.order_by('-is_featured', '-likes_count', '-created_at')

    return qs


def get_trending_posts(limit: int = 20) -> QuerySet:
    from django.utils import timezone
    from datetime import timedelta
    cutoff = timezone.now() - timedelta(days=7)
    return _base_published().filter(created_at__gte=cutoff).order_by('-likes_count', '-views_count')[:limit]


def get_following_feed(user) -> QuerySet:
    followed_ids = get_followed_creator_ids(user)
    qs = _base_published().filter(creator_id__in=followed_ids).order_by('-created_at')
    return _annotate_user_context(qs, user)


def get_creator_posts(creator_user, viewer=None) -> QuerySet:
    qs = _base_published().filter(creator=creator_user)
    if viewer and viewer.is_authenticated:
        qs = _annotate_user_context(qs, viewer)
    return qs


def get_saved_posts(user) -> QuerySet:
    saved_ids = SavedPost.objects.filter(user=user).values_list('post_id', flat=True)
    qs = _base_published().filter(id__in=saved_ids)
    return _annotate_user_context(qs, user)


def record_view(post: ContentPost, user=None, ip: str = None) -> None:
    from content_feed.models import PostView
    from django.db.models import F
    PostView.objects.create(post=post, user=user if (user and user.is_authenticated) else None, ip_address=ip)
    ContentPost.objects.filter(pk=post.pk).update(views_count=F('views_count') + 1)


def toggle_like(post: ContentPost, user) -> dict:
    from django.db.models import F
    like, created = PostLike.objects.get_or_create(user=user, post=post)
    if created:
        ContentPost.objects.filter(pk=post.pk).update(likes_count=F('likes_count') + 1)
    else:
        like.delete()
        ContentPost.objects.filter(pk=post.pk).update(likes_count=F('likes_count') - 1)
    post.refresh_from_db(fields=['likes_count'])
    return {'liked': created, 'likes_count': post.likes_count}


def toggle_save(post: ContentPost, user) -> dict:
    save, created = SavedPost.objects.get_or_create(user=user, post=post)
    if not created:
        save.delete()
    return {'saved': created}


def toggle_follow(follower, following_user) -> dict:
    if follower == following_user:
        raise ValueError("Cannot follow yourself.")
    follow, created = UserFollow.objects.get_or_create(follower=follower, following=following_user)
    if not created:
        follow.delete()
    return {'following': created}
