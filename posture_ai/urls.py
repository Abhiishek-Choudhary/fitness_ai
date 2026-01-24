from django.urls import path, include

from .views import AnalyzePostureAPIView, PushUpImageUploadAPI

urlpatterns = [
     path("pushup/upload/", PushUpImageUploadAPI.as_view()),
    path('analyze/<int:session_id>/', AnalyzePostureAPIView.as_view()),
]
