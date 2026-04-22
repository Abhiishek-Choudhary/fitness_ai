from django.core.management.base import BaseCommand
from payments.models import Plan

PLANS = [
    {
        'name': 'Free',
        'tier': 'free',
        'billing_cycle': 'monthly',
        'price_inr': 0,
        'description': 'Get started with basic fitness tracking.',
        'features': [
            '1 AI fitness plan per month',
            'Basic calorie tracking (5/day)',
            '10 workout sessions/month',
            'Progress tracking',
            'Gym news feed',
        ],
        'is_popular': False,
        'ai_plans_per_month': 1,
        'ai_regenerations_per_month': 0,
        'posture_analyses_per_month': 0,
        'calorie_estimates_per_day': 5,
        'workout_sessions_per_month': 10,
    },
    {
        'name': 'Pro Monthly',
        'tier': 'pro',
        'billing_cycle': 'monthly',
        'price_inr': 999,
        'description': 'Full access to all AI features. Most popular choice.',
        'features': [
            'Unlimited AI fitness plans',
            '5 AI plan regenerations/month',
            '10 posture analyses/month',
            'Unlimited calorie tracking',
            'Unlimited workout sessions',
            'Workout enrichment agent',
            'Priority gym news',
        ],
        'is_popular': True,
        'ai_plans_per_month': -1,
        'ai_regenerations_per_month': 5,
        'posture_analyses_per_month': 10,
        'calorie_estimates_per_day': -1,
        'workout_sessions_per_month': -1,
    },
    {
        'name': 'Pro Yearly',
        'tier': 'pro',
        'billing_cycle': 'yearly',
        'price_inr': 8999,
        'description': 'Pro plan billed yearly — save 25%.',
        'features': [
            'Everything in Pro Monthly',
            '2 months FREE (save ₹1,999)',
            'Early access to new features',
        ],
        'is_popular': False,
        'ai_plans_per_month': -1,
        'ai_regenerations_per_month': 5,
        'posture_analyses_per_month': 10,
        'calorie_estimates_per_day': -1,
        'workout_sessions_per_month': -1,
    },
    {
        'name': 'Elite Monthly',
        'tier': 'elite',
        'billing_cycle': 'monthly',
        'price_inr': 1999,
        'description': 'Maximum AI power for serious athletes.',
        'features': [
            'Everything in Pro',
            'Unlimited AI regenerations',
            'Unlimited posture analyses',
            'Advanced workout analytics',
            'Personalised nutrition coaching',
            'Priority support',
        ],
        'is_popular': False,
        'ai_plans_per_month': -1,
        'ai_regenerations_per_month': -1,
        'posture_analyses_per_month': -1,
        'calorie_estimates_per_day': -1,
        'workout_sessions_per_month': -1,
    },
    {
        'name': 'Elite Yearly',
        'tier': 'elite',
        'billing_cycle': 'yearly',
        'price_inr': 17999,
        'description': 'Elite plan billed yearly — save 25%.',
        'features': [
            'Everything in Elite Monthly',
            '2 months FREE (save ₹3,999)',
            'Dedicated onboarding session',
        ],
        'is_popular': False,
        'ai_plans_per_month': -1,
        'ai_regenerations_per_month': -1,
        'posture_analyses_per_month': -1,
        'calorie_estimates_per_day': -1,
        'workout_sessions_per_month': -1,
    },
]


class Command(BaseCommand):
    help = 'Seed subscription plans into the database'

    def handle(self, *args, **options):
        for plan_data in PLANS:
            obj, created = Plan.objects.update_or_create(
                tier=plan_data['tier'],
                billing_cycle=plan_data['billing_cycle'],
                defaults=plan_data,
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action}: {obj.name}'))
        self.stdout.write(self.style.SUCCESS('Plans seeded successfully.'))
