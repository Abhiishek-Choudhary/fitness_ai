from django.urls import path
from .views import enriched_workout_api

urlpatterns = [
    path("api/enriched-workout/", enriched_workout_api, name="enriched-workout"),
]
