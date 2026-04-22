from django.urls import path
from .views import (
    CalorieEstimateView,
    FoodLogCreateView,
    FoodLogFromEstimateView,
    FoodLogListView,
    FoodLogDeleteView,
)

urlpatterns = [
    path("estimate/", CalorieEstimateView.as_view(), name="calorie-estimate"),
    path("log/", FoodLogListView.as_view(), name="food-log-list"),
    path("log/create/", FoodLogCreateView.as_view(), name="food-log-create"),
    path("log/bulk/", FoodLogFromEstimateView.as_view(), name="food-log-bulk"),
    path("log/<int:pk>/", FoodLogDeleteView.as_view(), name="food-log-delete"),
]
