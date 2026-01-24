from django.urls import path
from .views import WorkoutListView, WorkoutSessionCreateView, WorkoutSessionListView

urlpatterns = [
    path('', WorkoutListView.as_view(), name='workout-list'),
    path('session/', WorkoutSessionCreateView.as_view(), name='workout-session-create'),
    path('session/list/', WorkoutSessionListView.as_view(), name='workout-session-list'),
]
