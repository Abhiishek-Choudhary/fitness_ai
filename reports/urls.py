from django.urls import path
from .views import (
    GenerateReportView,
    DownloadReportView,
    SendReportEmailView,
    ReportListView,
    ReportDetailView,
)

urlpatterns = [
    path('', ReportListView.as_view(), name='report-list'),
    path('generate/', GenerateReportView.as_view(), name='report-generate'),
    path('<int:pk>/', ReportDetailView.as_view(), name='report-detail'),
    path('<int:pk>/download/', DownloadReportView.as_view(), name='report-download'),
    path('<int:pk>/send-email/', SendReportEmailView.as_view(), name='report-send-email'),
]
