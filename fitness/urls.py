from django.urls import path
from .views import FitnessProfileView, PromptIntakeView, CalorieCalculatorView, NetCaloriesView, FitnessAIPlanView, FitnessAIPlanGetView, FitnessAIPlanRegenerateView

urlpatterns = [
    path('profile/', FitnessProfileView.as_view()),
    path('prompt/', PromptIntakeView.as_view()),
    path('calories/', CalorieCalculatorView.as_view()),       # existing
    path('calories/net/', NetCaloriesView.as_view(), name='net-calories'),
    path("ai-plan/", FitnessAIPlanView.as_view(), name="generate-ai-plan"),
    path("ai-plan/view/", FitnessAIPlanGetView.as_view(), name="view-ai-plan"), 
     path("ai-plan/regenerate/", FitnessAIPlanRegenerateView.as_view(), name="ai-plan-regenerate"),
]

