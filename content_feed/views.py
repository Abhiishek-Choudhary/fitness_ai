from django.contrib.auth.models import User
from django.db.models import F
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ContentPost, PostComment, CreatorProfile
from .permissions import IsCreatorOrReadOnly, IsCommentAuthorOrReadOnly
from .serializers import (
    PostCardSerializer, PostDetailSerializer, PostCreateSerializer,
    CommentSerializer, CommentCreateSerializer,
    CreatorProfileSerializer,
)
from .services import feed_service


# ── Pagination ────────────────────────────────────────────────────────────────

class FeedPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


# ── Feed endpoints ────────────────────────────────────────────────────────────

class PersonalizedFeedView(ListAPIView):
    """
    GET /api/feed/
    Personalized feed for authenticated users; falls back to engagement-sorted for anon.
    Query params: category, content_type, search, page, page_size
    """
    serializer_class = PostCardSerializer
    pagination_class = FeedPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return feed_service.get_personalized_feed(
            user=self.request.user,
            category=self.request.query_params.get('category'),
            content_type=self.request.query_params.get('content_type'),
            search=self.request.query_params.get('search'),
        )

    def get_serializer_context(self):
        return {**super().get_serializer_context(), 'request': self.request}


class TrendingFeedView(ListAPIView):
    """GET /api/feed/trending/ — most liked posts from the last 7 days."""
    serializer_class = PostCardSerializer
    pagination_class = FeedPagination
    permission_classes = [AllowAny]

    def get_queryset(self):
        return feed_service.get_trending_posts()


class FollowingFeedView(ListAPIView):
    """GET /api/feed/following/ — posts from creators the user follows."""
    serializer_class = PostCardSerializer
    pagination_class = FeedPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return feed_service.get_following_feed(self.request.user)


class SavedPostsFeedView(ListAPIView):
    """GET /api/feed/saved/ — user's bookmarked posts."""
    serializer_class = PostCardSerializer
    pagination_class = FeedPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return feed_service.get_saved_posts(self.request.user)


# ── Post CRUD ─────────────────────────────────────────────────────────────────

class PostListCreateView(APIView):
    """
    GET  /api/feed/posts/          — list all published posts (filtered/searched)
    POST /api/feed/posts/          — create a new post (auth required)
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = FeedPagination

    def get(self, request):
        qs = feed_service.get_personalized_feed(
            user=request.user,
            category=request.query_params.get('category'),
            content_type=request.query_params.get('content_type'),
            search=request.query_params.get('search'),
        )
        paginator = FeedPagination()
        page = paginator.paginate_queryset(qs, request)
        serializer = PostCardSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        serializer = PostCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = serializer.save(creator=request.user)
        return Response(PostDetailSerializer(post, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)


class PostDetailView(APIView):
    """
    GET    /api/feed/posts/<id>/
    PUT    /api/feed/posts/<id>/   (creator only)
    DELETE /api/feed/posts/<id>/   (creator only)
    """
    permission_classes = [IsAuthenticatedOrReadOnly, IsCreatorOrReadOnly]

    def _get_post(self, pk, user):
        try:
            return ContentPost.objects.select_related(
                'creator', 'creator__creator_profile'
            ).prefetch_related('tags').get(pk=pk, status='published')
        except ContentPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_post(pk, request.user)
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Record view asynchronously-safe (simple counter update)
        ip = request.META.get('REMOTE_ADDR')
        feed_service.record_view(post, user=request.user, ip=ip)

        return Response(PostDetailSerializer(post, context={'request': request}).data)

    def put(self, request, pk):
        post = self._get_post(pk, request.user)
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, post)
        serializer = PostCreateSerializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PostDetailSerializer(post, context={'request': request}).data)

    def delete(self, request, pk):
        post = self._get_post(pk, request.user)
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, post)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Social interaction endpoints ──────────────────────────────────────────────

class PostLikeToggleView(APIView):
    """POST /api/feed/posts/<id>/like/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = ContentPost.objects.get(pk=pk, status='published')
        except ContentPost.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        result = feed_service.toggle_like(post, request.user)
        return Response(result)


class PostSaveToggleView(APIView):
    """POST /api/feed/posts/<id>/save/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            post = ContentPost.objects.get(pk=pk, status='published')
        except ContentPost.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        result = feed_service.toggle_save(post, request.user)
        return Response(result)


# ── Comments ──────────────────────────────────────────────────────────────────

class PostCommentListCreateView(APIView):
    """
    GET  /api/feed/posts/<id>/comments/
    POST /api/feed/posts/<id>/comments/
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def _get_post(self, pk):
        try:
            return ContentPost.objects.get(pk=pk, status='published')
        except ContentPost.DoesNotExist:
            return None

    def get(self, request, pk):
        post = self._get_post(pk)
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        # Top-level comments only (replies are nested)
        comments = post.comments.filter(parent=None).select_related('user', 'user__creator_profile').prefetch_related('replies__user')
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, pk):
        post = self._get_post(pk)
        if not post:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(user=request.user, post=post)
        # Update denormalized counter
        ContentPost.objects.filter(pk=pk).update(comments_count=F('comments_count') + 1)
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentDetailView(APIView):
    """DELETE /api/feed/comments/<id>/ (author only)"""
    permission_classes = [IsAuthenticated, IsCommentAuthorOrReadOnly]

    def delete(self, request, pk):
        try:
            comment = PostComment.objects.get(pk=pk)
        except PostComment.DoesNotExist:
            return Response({'error': 'Comment not found.'}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, comment)
        post_id = comment.post_id
        comment.delete()
        ContentPost.objects.filter(pk=post_id).update(
            comments_count=F('comments_count') - 1
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


# ── Creator / Follow endpoints ────────────────────────────────────────────────

class CreatorProfileView(APIView):
    """GET /api/feed/creators/<username>/"""
    permission_classes = [AllowAny]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
            profile = user.creator_profile
        except (User.DoesNotExist, CreatorProfile.DoesNotExist):
            return Response({'error': 'Creator not found.'}, status=status.HTTP_404_NOT_FOUND)

        posts = feed_service.get_creator_posts(user, viewer=request.user)
        paginator = FeedPagination()
        page = paginator.paginate_queryset(posts, request)
        return Response({
            'profile': CreatorProfileSerializer(profile).data,
            'posts': paginator.get_paginated_response(
                PostCardSerializer(page, many=True, context={'request': request}).data
            ).data,
        })


class FollowToggleView(APIView):
    """POST /api/feed/creators/<username>/follow/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, username):
        try:
            target = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            result = feed_service.toggle_follow(request.user, target)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result)


class MyFollowingListView(ListAPIView):
    """GET /api/feed/following/creators/ — list of creators the user follows."""
    permission_classes = [IsAuthenticated]
    serializer_class = CreatorProfileSerializer

    def get_queryset(self):
        from .models import UserFollow
        followed_ids = UserFollow.objects.filter(
            follower=self.request.user
        ).values_list('following_id', flat=True)
        return CreatorProfile.objects.filter(user_id__in=followed_ids).select_related('user')


class FeedCategoryListView(APIView):
    """GET /api/feed/categories/ — available fitness categories with post counts."""
    permission_classes = [AllowAny]

    def get(self, request):
        from django.db.models import Count
        counts = (
            ContentPost.objects
            .filter(status='published')
            .values('fitness_category')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        return Response([
            {'category': row['fitness_category'], 'count': row['count']}
            for row in counts
        ])
