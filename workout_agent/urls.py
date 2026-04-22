from django.urls import path
from .views import EnrichedWorkoutAPIView

urlpatterns = [
    path("api/enriched-workout/", EnrichedWorkoutAPIView.as_view(), name="enriched-workout"),
]
