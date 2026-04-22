from django.urls import path
from .views import GymNewsListView, GymNewsCategoryView, GymNewsCategoriesView

urlpatterns = [
    path("", GymNewsListView.as_view(), name="gym-news-list"),
    path("categories/", GymNewsCategoriesView.as_view(), name="gym-news-categories"),
    path("<str:category>/", GymNewsCategoryView.as_view(), name="gym-news-category"),
]
