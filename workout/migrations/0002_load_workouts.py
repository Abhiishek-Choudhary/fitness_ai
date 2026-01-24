from django.db import migrations

def create_workouts(apps, schema_editor):
    Workout = apps.get_model('workout', 'Workout')
    workouts = [
        {"name": "Walking", "workout_type": "cardio", "met": 3.5},
        {"name": "Jogging", "workout_type": "cardio", "met": 7},
        {"name": "Running", "workout_type": "cardio", "met": 9},
        {"name": "Cycling", "workout_type": "cardio", "met": 8},
        {"name": "Weight Training", "workout_type": "strength", "met": 4},
        {"name": "HIIT", "workout_type": "hiit", "met": 10},
        {"name": "Yoga", "workout_type": "yoga", "met": 2.5},
    ]
    for w in workouts:
        Workout.objects.create(**w)

class Migration(migrations.Migration):

    dependencies = [
        ('workout', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_workouts),
    ]
