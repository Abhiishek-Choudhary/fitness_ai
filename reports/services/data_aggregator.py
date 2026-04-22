"""Collect all user data for the report period."""
from datetime import date
from django.db.models import Sum, Avg, Count

from workout.models import WorkoutSession
from calorie_ai.models import FoodLog
from dashboard.models import ProgressEntry
from fitness.models import FitnessProfile, FitnessAIPlan


def aggregate_report_data(user, period_start: date, period_end: date) -> dict:
    workout_sessions = WorkoutSession.objects.filter(
        user=user, date__range=(period_start, period_end)
    ).select_related('workout').order_by('date')

    food_logs = FoodLog.objects.filter(
        user=user, logged_on__range=(period_start, period_end)
    ).order_by('logged_on', 'meal_type')

    progress_entries = ProgressEntry.objects.filter(
        user=user, recorded_on__range=(period_start, period_end)
    ).order_by('recorded_on')

    try:
        profile = FitnessProfile.objects.get(user=user)
    except FitnessProfile.DoesNotExist:
        profile = None

    latest_plan = FitnessAIPlan.objects.filter(user=user).order_by('-created_at').first()

    # --- Workout stats ---
    workout_stats = workout_sessions.aggregate(
        total_sessions=Count('id'),
        total_minutes=Sum('duration_minutes'),
        total_calories_burned=Sum('calories_burned'),
    )
    workout_stats['total_sessions'] = workout_stats['total_sessions'] or 0
    workout_stats['total_minutes'] = workout_stats['total_minutes'] or 0
    workout_stats['total_calories_burned'] = round(workout_stats['total_calories_burned'] or 0, 1)

    by_type = {}
    for s in workout_sessions:
        t = s.workout.workout_type
        by_type.setdefault(t, {'sessions': 0, 'minutes': 0, 'calories': 0})
        by_type[t]['sessions'] += 1
        by_type[t]['minutes'] += s.duration_minutes
        by_type[t]['calories'] += s.calories_burned or 0

    workout_sessions_list = [
        {
            'date': str(s.date),
            'workout': s.workout.name,
            'type': s.workout.workout_type,
            'duration_min': s.duration_minutes,
            'calories_burned': round(s.calories_burned or 0, 1),
        }
        for s in workout_sessions
    ]

    # --- Nutrition stats ---
    food_stats = food_logs.aggregate(
        total_calories_in=Sum('calories'),
        total_protein=Sum('protein_g'),
        total_carbs=Sum('carbs_g'),
        total_fat=Sum('fat_g'),
    )
    food_stats = {k: round(v or 0, 1) for k, v in food_stats.items()}

    days_logged = food_logs.values('logged_on').distinct().count()
    food_stats['days_with_food_log'] = days_logged
    food_stats['avg_daily_calories'] = (
        round(food_stats['total_calories_in'] / days_logged, 1) if days_logged else 0
    )

    food_by_day = {}
    for log in food_logs:
        key = str(log.logged_on)
        food_by_day.setdefault(key, {'total_calories': 0, 'items': []})
        food_by_day[key]['total_calories'] += log.calories
        food_by_day[key]['items'].append({
            'name': log.food_name,
            'meal_type': log.meal_type,
            'calories': log.calories,
            'quantity': log.quantity_description,
        })

    # --- Progress stats ---
    progress_list = [
        {'date': str(e.recorded_on), 'weight_kg': float(e.weight) if e.weight else None, 'note': e.note}
        for e in progress_entries
    ]
    weights = [float(e.weight) for e in progress_entries if e.weight]
    weight_change = round(weights[-1] - weights[0], 2) if len(weights) >= 2 else None
    start_weight = weights[0] if weights else None
    end_weight = weights[-1] if weights else None

    # --- Calorie balance ---
    net_calories = round(food_stats['total_calories_in'] - workout_stats['total_calories_burned'], 1)

    return {
        'user': {
            'name': user.get_full_name() or user.username or user.email.split('@')[0],
            'email': user.email,
        },
        'profile': {
            'age': profile.age if profile else None,
            'gender': profile.gender if profile else None,
            'height_cm': profile.height_cm if profile else None,
            'weight_kg': profile.weight_kg if profile else None,
            'fitness_goal': profile.fitness_goal if profile else None,
            'fitness_level': profile.fitness_level if profile else None,
            'activity_level': profile.activity_level if profile else None,
        },
        'workouts': {
            'stats': workout_stats,
            'by_type': by_type,
            'sessions': workout_sessions_list,
        },
        'nutrition': {
            'stats': food_stats,
            'by_day': food_by_day,
        },
        'progress': {
            'entries': progress_list,
            'start_weight': start_weight,
            'end_weight': end_weight,
            'weight_change': weight_change,
        },
        'calorie_balance': {
            'total_consumed': food_stats['total_calories_in'],
            'total_burned': workout_stats['total_calories_burned'],
            'net': net_calories,
        },
        'ai_plan_exists': latest_plan is not None,
    }
