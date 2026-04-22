from django.urls import path
from .views import (
    PersonalizedFeedView,
    TrendingFeedView,
    FollowingFeedView,
    SavedPostsFeedView,
    PostListCreateView,
    PostDetailView,
    PostLikeToggleView,
    PostSaveToggleView,
    PostCommentListCreateView,
    CommentDetailView,
    CreatorProfileView,
    FollowToggleView,
    MyFollowingListView,
    FeedCategoryListView,
)

urlpatterns = [
    # ── Feeds ──────────────────────────────────────────────────────────────────
    path('',                    PersonalizedFeedView.as_view(),   name='feed-home'),
    path('trending/',           TrendingFeedView.as_view(),        name='feed-trending'),
    path('following/',          FollowingFeedView.as_view(),       name='feed-following'),
    path('saved/',              SavedPostsFeedView.as_view(),      name='feed-saved'),
    path('categories/',         FeedCategoryListView.as_view(),    name='feed-categories'),

    # ── Posts ──────────────────────────────────────────────────────────────────
    path('posts/',              PostListCreateView.as_view(),      name='post-list-create'),
    path('posts/<int:pk>/',     PostDetailView.as_view(),          name='post-detail'),
    path('posts/<int:pk>/like/',PostLikeToggleView.as_view(),      name='post-like'),
    path('posts/<int:pk>/save/',PostSaveToggleView.as_view(),      name='post-save'),

    # ── Comments ───────────────────────────────────────────────────────────────
    path('posts/<int:pk>/comments/', PostCommentListCreateView.as_view(), name='post-comments'),
    path('comments/<int:pk>/',       CommentDetailView.as_view(),          name='comment-delete'),

    # ── Creators & Follow ──────────────────────────────────────────────────────
    path('creators/<str:username>/',         CreatorProfileView.as_view(), name='creator-profile'),
    path('creators/<str:username>/follow/',  FollowToggleView.as_view(),   name='creator-follow'),
    path('following/creators/',              MyFollowingListView.as_view(), name='my-following'),
]
