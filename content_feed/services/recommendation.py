"""
Recommendation engine — maps user profile/activity to content categories
and computes a ranked queryset. Single Responsibility: scoring only.
"""
import math
from datetime import timedelta
from django.utils import timezone
from django.db.models import QuerySet, F, ExpressionWrapper, FloatField, Case, When, Value

# Maps fitness goal → preferred content categories (ordered by relevance)
GOAL_CATEGORY_MAP = {
    'WEIGHT_LOSS':      ['weight_loss', 'cardio', 'hiit', 'nutrition'],
    'MUSCLE_GAIN':      ['muscle_gain', 'strength', 'nutrition'],
    'ENDURANCE':        ['cardio', 'hiit', 'flexibility', 'general'],
    'GENERAL_FITNESS':  ['general', 'cardio', 'strength', 'flexibility'],
}

# Maps workout session types → preferred categories
WORKOUT_CATEGORY_MAP = {
    'cardio':       ['cardio', 'hiit', 'weight_loss'],
    'strength':     ['strength', 'muscle_gain'],
    'flexibility':  ['flexibility', 'yoga'],
    'hiit':         ['hiit', 'cardio', 'weight_loss'],
    'yoga':         ['yoga', 'flexibility'],
}

# Maps activity level → difficulty preference
ACTIVITY_DIFFICULTY_MAP = {
    'sedentary': ['beginner'],
    'light':     ['beginner', 'intermediate'],
    'moderate':  ['intermediate'],
    'heavy':     ['intermediate', 'advanced'],
    'athlete':   ['advanced'],
}


def get_preferred_categories(user) -> list[str]:
    try:
        profile = user.fitness_profile
        categories = list(GOAL_CATEGORY_MAP.get(profile.fitness_goal, ['general']))

        # Enrich from recent workout types (last 30 days)
        recent_types = (
            user.workout_sessions
            .filter(date__gte=(timezone.now().date() - timedelta(days=30)))
            .values_list('workout__workout_type', flat=True)
            .distinct()
        )
        for wtype in recent_types:
            for cat in WORKOUT_CATEGORY_MAP.get(wtype, []):
                if cat not in categories:
                    categories.append(cat)

        return categories
    except Exception:
        return ['general', 'cardio', 'strength']


def get_preferred_difficulties(user) -> list[str]:
    try:
        activity = user.fitness_profile.activity_level
        return ACTIVITY_DIFFICULTY_MAP.get(activity, ['beginner', 'intermediate'])
    except Exception:
        return ['beginner', 'intermediate']


def get_followed_creator_ids(user) -> list[int]:
    from content_feed.models import UserFollow
    return list(
        UserFollow.objects.filter(follower=user).values_list('following_id', flat=True)
    )


def rank_feed_queryset(qs: QuerySet, user) -> QuerySet:
    """
    Annotate and order the queryset by a composite score:
      - followed creator bonus
      - category relevance bonus
      - difficulty match bonus
      - engagement (likes + comments)
      - recency (posts older than 7 days get lower rank)
    """
    from content_feed.models import ContentPost

    preferred_cats = get_preferred_categories(user)
    preferred_diffs = get_preferred_difficulties(user)
    followed_ids = get_followed_creator_ids(user)

    # Category match: rank by position in preferred list
    cat_whens = [
        When(fitness_category=cat, then=Value(len(preferred_cats) - i))
        for i, cat in enumerate(preferred_cats)
    ]
    diff_whens = [
        When(difficulty=diff, then=Value(2))
        for diff in preferred_diffs
    ]
    followed_when = When(creator_id__in=followed_ids, then=Value(10)) if followed_ids else None

    cases = []
    if followed_when:
        cases.append(ExpressionWrapper(
            Case(followed_when, default=Value(0)),
            output_field=FloatField()
        ))
    if cat_whens:
        cases.append(ExpressionWrapper(
            Case(*cat_whens, default=Value(0)),
            output_field=FloatField()
        ))
    if diff_whens:
        cases.append(ExpressionWrapper(
            Case(*diff_whens, default=Value(0)),
            output_field=FloatField()
        ))

    # Sort: featured first, then by likes+comments (engagement proxy), then recency
    return qs.order_by(
        '-is_featured',
        Case(*(cat_whens if cat_whens else []), default=Value(0)).desc(),
        Case(*(diff_whens if diff_whens else []), default=Value(0)).desc(),
        '-likes_count',
        '-created_at',
    )
