"""
Management command: seed_content
Fetches real fitness videos from YouTube and creates ContentPost + CreatorProfile records.
Usage:  python manage.py seed_content
        python manage.py seed_content --flush   (wipe seeded posts first)
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from content_feed.models import ContentPost, CreatorProfile, Tag
from content_feed.services.youtube_fetcher import SEED_CATALOGUE, search_videos, fetch_video_duration

# Dummy creator personas (will be created if they don't exist)
CREATOR_PERSONAS = [
    {
        'username': 'coach_alex',
        'email': 'coach.alex@fitnessai.seed',
        'first_name': 'Alex',
        'last_name': 'Carter',
        'bio': 'NASM-certified personal trainer | 10+ years helping people transform their bodies.',
        'specialization': 'Strength & Conditioning',
        'is_verified': True,
        'avatar_url': 'https://i.pravatar.cc/150?img=11',
    },
    {
        'username': 'yoga_priya',
        'email': 'yoga.priya@fitnessai.seed',
        'first_name': 'Priya',
        'last_name': 'Sharma',
        'bio': 'RYT-500 Yoga instructor | Mindful movement for every body.',
        'specialization': 'Yoga & Flexibility',
        'is_verified': True,
        'avatar_url': 'https://i.pravatar.cc/150?img=5',
    },
    {
        'username': 'hiit_king',
        'email': 'hiit.king@fitnessai.seed',
        'first_name': 'Marcus',
        'last_name': 'Johnson',
        'bio': 'Ex-pro athlete | HIIT & metabolic conditioning specialist.',
        'specialization': 'HIIT & Fat Loss',
        'is_verified': True,
        'avatar_url': 'https://i.pravatar.cc/150?img=15',
    },
    {
        'username': 'nutrition_nisha',
        'email': 'nutrition.nisha@fitnessai.seed',
        'first_name': 'Nisha',
        'last_name': 'Patel',
        'bio': 'Registered Dietitian | Making healthy eating simple and delicious.',
        'specialization': 'Sports Nutrition',
        'is_verified': False,
        'avatar_url': 'https://i.pravatar.cc/150?img=9',
    },
    {
        'username': 'run_coach_sam',
        'email': 'run.coach.sam@fitnessai.seed',
        'first_name': 'Sam',
        'last_name': 'Williams',
        'bio': 'Marathon runner | Helping everyday athletes go the distance.',
        'specialization': 'Cardio & Endurance',
        'is_verified': False,
        'avatar_url': 'https://i.pravatar.cc/150?img=3',
    },
]

CATEGORY_CREATOR_MAP = {
    'weight_loss': 'hiit_king',
    'hiit': 'hiit_king',
    'muscle_gain': 'coach_alex',
    'strength': 'coach_alex',
    'yoga': 'yoga_priya',
    'flexibility': 'yoga_priya',
    'nutrition': 'nutrition_nisha',
    'cardio': 'run_coach_sam',
    'general': 'coach_alex',
}

CATEGORY_TAGS = {
    'weight_loss': ['weight-loss', 'fat-burn', 'cardio'],
    'hiit': ['hiit', 'interval-training', 'fat-burn'],
    'muscle_gain': ['muscle', 'bodybuilding', 'strength'],
    'strength': ['strength', 'powerlifting', 'weights'],
    'yoga': ['yoga', 'mindfulness', 'flexibility'],
    'flexibility': ['stretching', 'mobility', 'recovery'],
    'nutrition': ['nutrition', 'meal-prep', 'diet'],
    'cardio': ['cardio', 'running', 'endurance'],
    'general': ['fitness', 'health', 'workout'],
}


class Command(BaseCommand):
    help = 'Seed fitness content from YouTube into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Delete all previously seeded posts before re-seeding'
        )

    def handle(self, *args, **options):
        api_key = os.getenv('YOUTUBE_API_KEY', '')
        if not api_key:
            self.stderr.write(self.style.ERROR('YOUTUBE_API_KEY not set in environment.'))
            return

        if options['flush']:
            deleted, _ = ContentPost.objects.filter(source='youtube_seed').delete()
            self.stdout.write(self.style.WARNING(f'Flushed {deleted} seeded posts.'))

        creators = self._ensure_creators()
        total = 0

        for query, category, difficulty, content_type, count in SEED_CATALOGUE:
            self.stdout.write(f'\n  Fetching: "{query}" …')
            videos = search_videos(api_key, query, max_results=count)

            if not videos:
                self.stdout.write(self.style.WARNING(f'  No results for "{query}"'))
                continue

            # Batch-fetch durations
            video_ids = [v['youtube_video_id'] for v in videos]
            durations = fetch_video_duration(api_key, video_ids)

            creator_username = CATEGORY_CREATOR_MAP.get(category, 'coach_alex')
            creator = creators[creator_username]
            tags = self._get_or_create_tags(CATEGORY_TAGS.get(category, ['fitness']))

            for video in videos:
                vid_id = video['youtube_video_id']
                if ContentPost.objects.filter(youtube_video_id=vid_id).exists():
                    self.stdout.write(f'    Skip (exists): {vid_id}')
                    continue

                post = ContentPost.objects.create(
                    creator=creator,
                    title=video['title'][:200],
                    body=video['body'],
                    content_type=content_type,
                    fitness_category=category,
                    difficulty=difficulty,
                    thumbnail_url=video['thumbnail_url'],
                    video_url=f"https://www.youtube.com/watch?v={vid_id}",
                    youtube_video_id=vid_id,
                    duration_seconds=durations.get(vid_id),
                    status='published',
                    source='youtube_seed',
                )
                post.tags.set(tags)
                safe_title = post.title[:60].encode('ascii', errors='replace').decode('ascii')
                self.stdout.write(self.style.SUCCESS(f'    + {safe_title}'))
                total += 1

        self.stdout.write(self.style.SUCCESS(f'\nDone. Created {total} posts.'))

    def _ensure_creators(self) -> dict:
        creators = {}
        for persona in CREATOR_PERSONAS:
            user, created = User.objects.get_or_create(
                username=persona['username'],
                defaults={
                    'email': persona['email'],
                    'first_name': persona['first_name'],
                    'last_name': persona['last_name'],
                    'is_active': True,
                },
            )
            if created:
                user.set_unusable_password()
                user.save()

            CreatorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'bio': persona['bio'],
                    'specialization': persona['specialization'],
                    'is_verified': persona['is_verified'],
                    'avatar_url': persona['avatar_url'],
                },
            )
            creators[persona['username']] = user
            label = 'Created' if created else 'Found'
            self.stdout.write(f'  [{label}] @{user.username}')
        return creators

    def _get_or_create_tags(self, names: list) -> list:
        tags = []
        for name in names:
            tag, _ = Tag.objects.get_or_create(name=name)
            tags.append(tag)
        return tags
