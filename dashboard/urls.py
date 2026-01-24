from django.urls import path
from dashboard.views import (
    ProgressEntryCreateAPIView,
    ProgressEntryListAPIView,
    ProgressEntryDeleteAPIView,
)

urlpatterns = [
    # Create or update a progress entry (POST)
    path("progress/", ProgressEntryCreateAPIView.as_view(), name="progress-create"),

    # List all progress entries (GET)
    path("progress/list/", ProgressEntryListAPIView.as_view(), name="progress-list"),

    # Delete a specific progress entry (DELETE)
    path("progress/<int:pk>/", ProgressEntryDeleteAPIView.as_view(), name="progress-delete"),
]
