"""
Seed realistic community data: locations, events, groups.
Usage: python manage.py seed_community
       python manage.py seed_community --flush
"""
import random
from datetime import date, timedelta, time
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from community.models import (
    UserLocation, FitnessEvent, EventAttendee,
    CommunityGroup, GroupMember,
)

CITY_DATA = [
    ('Mumbai',    'Maharashtra', 'India', 19.0760,  72.8777),
    ('Delhi',     'Delhi',       'India', 28.6139,  77.2090),
    ('Bangalore', 'Karnataka',   'India', 12.9716,  77.5946),
    ('Hyderabad', 'Telangana',   'India', 17.3850,  78.4867),
    ('Chennai',   'Tamil Nadu',  'India', 13.0827,  80.2707),
    ('Pune',      'Maharashtra', 'India', 18.5204,  73.8567),
]

EVENTS_DATA = [
    {
        'title': 'Sunday Morning 10K Run',
        'description': 'Join us for a scenic 10K run through the city park. All paces welcome!',
        'activity_type': 'running', 'difficulty': 'intermediate',
        'venue_name': 'Central Park Main Gate', 'days_ahead': 3,
        'start_time': time(6, 30), 'end_time': time(8, 30),
        'max_participants': 50,
    },
    {
        'title': 'Sunrise Outdoor Yoga',
        'description': 'Start your week right with a free sunrise yoga session on the beach.',
        'activity_type': 'outdoor_yoga', 'difficulty': 'all',
        'venue_name': 'Marine Drive', 'days_ahead': 5,
        'start_time': time(6, 0), 'end_time': time(7, 0),
        'max_participants': 30,
    },
    {
        'title': 'HIIT Bootcamp — Fat Burn Saturday',
        'description': 'High-intensity interval training session. Bring water & a towel.',
        'activity_type': 'outdoor_hiit', 'difficulty': 'intermediate',
        'venue_name': 'Sports Complex Grounds', 'days_ahead': 7,
        'start_time': time(7, 0), 'end_time': time(8, 0),
        'max_participants': 20,
    },
    {
        'title': 'Evening Cycling — 30 km Loop',
        'description': 'Casual evening ride through the highway loop. Helmet mandatory.',
        'activity_type': 'cycling', 'difficulty': 'intermediate',
        'venue_name': 'Eastern Highway Start Point', 'days_ahead': 4,
        'start_time': time(17, 30), 'end_time': time(20, 0),
        'max_participants': 25,
    },
    {
        'title': "Women's Strength Training Circle",
        'description': 'A safe, supportive environment for women to lift together.',
        'activity_type': 'gym_meetup', 'difficulty': 'beginner',
        'venue_name': 'FitLife Gym', 'days_ahead': 6,
        'start_time': time(9, 0), 'end_time': time(10, 30),
        'max_participants': 15,
    },
    {
        'title': 'Trail Hiking — Valley Circuit',
        'description': 'Moderate 12 km trail hike. Beautiful views at the summit.',
        'activity_type': 'hiking', 'difficulty': 'intermediate',
        'venue_name': 'Valley Trail Head', 'days_ahead': 10,
        'start_time': time(5, 30), 'end_time': time(11, 0),
        'max_participants': 20,
    },
    {
        'title': 'Beginner 5K Walk & Run',
        'description': 'Perfect for new runners. Walk when you need to, run when you can!',
        'activity_type': 'running', 'difficulty': 'beginner',
        'venue_name': 'Riverside Promenade', 'days_ahead': 2,
        'start_time': time(7, 0), 'end_time': time(8, 30),
        'max_participants': 40,
    },
    {
        'title': 'CrossFit Open Community WOD',
        'description': 'Open CrossFit workout of the day. All levels welcome.',
        'activity_type': 'crossfit', 'difficulty': 'advanced',
        'venue_name': 'CrossFit Box — Sector 14', 'days_ahead': 8,
        'start_time': time(8, 0), 'end_time': time(9, 30),
        'max_participants': None,
    },
]

GROUPS_DATA = [
    {
        'name': 'Mumbai Runners Club',
        'description': 'The largest running community in Mumbai. Weekly runs, races, and more!',
        'activity_focus': 'running', 'difficulty': 'all', 'privacy': 'public',
        'city': 'Mumbai',
    },
    {
        'name': 'Bangalore Cyclists',
        'description': 'Weekend rides, daily commuters, and everything in between.',
        'activity_focus': 'cycling', 'difficulty': 'intermediate', 'privacy': 'public',
        'city': 'Bangalore',
    },
    {
        'name': 'Delhi HIIT Warriors',
        'description': 'Early morning HIIT sessions across Delhi parks. No excuses.',
        'activity_focus': 'outdoor_hiit', 'difficulty': 'intermediate', 'privacy': 'public',
        'city': 'Delhi',
    },
    {
        'name': 'Pune Yoga & Wellness',
        'description': 'Outdoor yoga, meditation and mindful living community.',
        'activity_focus': 'outdoor_yoga', 'difficulty': 'all', 'privacy': 'public',
        'city': 'Pune',
    },
    {
        'name': 'Hyderabad Trail Hikers',
        'description': 'Exploring Telangana trails every weekend. Safety first!',
        'activity_focus': 'hiking', 'difficulty': 'intermediate', 'privacy': 'public',
        'city': 'Hyderabad',
    },
    {
        'name': 'Chennai Strength & Powerlifting',
        'description': 'Serious lifters only. Member-approved access.',
        'activity_focus': 'gym_meetup', 'difficulty': 'advanced', 'privacy': 'private',
        'city': 'Chennai',
    },
    {
        'name': 'All India Crossfitters',
        'description': 'Connect CrossFit athletes across the country.',
        'activity_focus': 'crossfit', 'difficulty': 'advanced', 'privacy': 'public',
        'city': 'Bangalore',
    },
    {
        'name': 'Morning Walk Friends',
        'description': 'Simple daily morning walks. Great for stress relief and weight loss.',
        'activity_focus': 'walking', 'difficulty': 'beginner', 'privacy': 'public',
        'city': 'Mumbai',
    },
]


class Command(BaseCommand):
    help = 'Seed community events, groups, and locations'

    def add_arguments(self, parser):
        parser.add_argument('--flush', action='store_true', help='Clear seeded data first')

    def handle(self, *args, **options):
        if options['flush']:
            FitnessEvent.objects.filter(source='seed').delete()
            CommunityGroup.objects.filter(description__startswith='The largest running').delete()
            self.stdout.write(self.style.WARNING('Flushed community seed data.'))

        seed_users = self._get_or_create_seed_users()
        self._seed_locations(seed_users)
        self._seed_events(seed_users)
        self._seed_groups(seed_users)
        self.stdout.write(self.style.SUCCESS('\nCommunity seed complete.'))

    def _get_or_create_seed_users(self):
        usernames = ['coach_alex', 'yoga_priya', 'hiit_king', 'nutrition_nisha', 'run_coach_sam']
        users = []
        for uname in usernames:
            user, _ = User.objects.get_or_create(username=uname)
            users.append(user)
        self.stdout.write(f'  Using {len(users)} seed creator accounts.')
        return users

    def _seed_locations(self, users):
        for i, user in enumerate(users):
            city_data = CITY_DATA[i % len(CITY_DATA)]
            city, state, country, lat, lon = city_data
            # Add small random offset so they're not all on the same spot
            lat += random.uniform(-0.05, 0.05)
            lon += random.uniform(-0.05, 0.05)
            UserLocation.objects.update_or_create(
                user=user,
                defaults={
                    'city': city, 'state': state, 'country': country,
                    'latitude': round(lat, 6), 'longitude': round(lon, 6),
                    'visibility': 'public',
                },
            )
        self.stdout.write(self.style.SUCCESS(f'  Seeded {len(users)} user locations.'))

    def _seed_events(self, users):
        today = date.today()
        count = 0
        for i, event_data in enumerate(EVENTS_DATA):
            organizer = users[i % len(users)]
            city, state, country, base_lat, base_lon = CITY_DATA[i % len(CITY_DATA)]
            lat = base_lat + random.uniform(-0.02, 0.02)
            lon = base_lon + random.uniform(-0.02, 0.02)
            event_date = today + timedelta(days=event_data['days_ahead'])

            event, created = FitnessEvent.objects.get_or_create(
                title=event_data['title'],
                organizer=organizer,
                defaults={
                    'event_date': event_date,
                    'description': event_data['description'],
                    'activity_type': event_data['activity_type'],
                    'difficulty': event_data['difficulty'],
                    'venue_name': event_data['venue_name'],
                    'city': city, 'state': state, 'country': country,
                    'latitude': round(lat, 6), 'longitude': round(lon, 6),
                    'start_time': event_data['start_time'],
                    'end_time': event_data.get('end_time'),
                    'max_participants': event_data.get('max_participants'),
                    'status': 'upcoming',
                    'privacy': 'public',
                },
            )
            if created:
                # Auto-RSVP organiser
                EventAttendee.objects.get_or_create(
                    event=event, user=organizer,
                    defaults={'rsvp_status': 'going'}
                )
                FitnessEvent.objects.filter(pk=event.pk).update(attendees_count=1)
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  Seeded {count} events.'))

    def _seed_groups(self, users):
        count = 0
        for i, gdata in enumerate(GROUPS_DATA):
            creator = users[i % len(users)]
            group, created = CommunityGroup.objects.get_or_create(
                name=gdata['name'],
                defaults={
                    'creator': creator,
                    'description': gdata['description'],
                    'activity_focus': gdata['activity_focus'],
                    'difficulty': gdata['difficulty'],
                    'privacy': gdata['privacy'],
                    'city': gdata['city'],
                    'country': 'India',
                },
            )
            if created:
                GroupMember.objects.get_or_create(
                    group=group, user=creator,
                    defaults={'role': 'admin', 'status': 'active'}
                )
                # Add a few more seed users as members
                for u in random.sample(users, min(3, len(users))):
                    if u != creator:
                        m, mc = GroupMember.objects.get_or_create(
                            group=group, user=u,
                            defaults={'role': 'member', 'status': 'active'}
                        )
                        if mc:
                            CommunityGroup.objects.filter(pk=group.pk).update(
                                members_count=group.members_count + 1
                            )
                CommunityGroup.objects.filter(pk=group.pk).update(members_count=4)
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  Seeded {count} groups.'))
