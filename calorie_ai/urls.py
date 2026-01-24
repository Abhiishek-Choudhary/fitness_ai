from django.urls import path
from .views import CalorieEstimateView

urlpatterns = [
    path("estimate/", CalorieEstimateView.as_view(), name="calorie-estimate"),
]
