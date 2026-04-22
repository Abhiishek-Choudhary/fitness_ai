import logging
from datetime import date, timedelta
from calendar import monthrange

from django.http import FileResponse, HttpResponse
from django.utils import timezone
from django.core.files.base import ContentFile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import GeneratedReport
from .serializers import (
    GenerateReportSerializer, GeneratedReportSerializer, SendReportEmailSerializer
)
from .services.data_aggregator import aggregate_report_data
from .services.ai_analyzer import generate_ai_analysis
from .services.pdf_generator import generate_pdf
from .services.email_service import send_report_email

logger = logging.getLogger(__name__)


def _resolve_period(period: str, year: int, month: int = None, week: int = None):
    """Return (period_start, period_end) dates."""
    if period == 'weekly':
        # ISO week: Monday–Sunday
        start = date.fromisocalendar(year, week, 1)
        end = start + timedelta(days=6)
    else:
        # monthly
        start = date(year, month, 1)
        end = date(year, month, monthrange(year, month)[1])
    return start, end


class GenerateReportView(APIView):
    """
    POST /api/reports/generate/
    Body: { "period": "weekly"|"monthly", "year": 2025, "month": 4 }
           or { "period": "weekly", "year": 2025, "week": 16 }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        period = data['period']
        year = data['year']
        month = data.get('month')
        week = data.get('week')

        try:
            period_start, period_end = _resolve_period(period, year, month, week)
        except Exception:
            return Response({'error': 'Invalid period parameters.'}, status=status.HTTP_400_BAD_REQUEST)

        if period_end > date.today():
            return Response(
                {'error': 'Cannot generate a report for a future period.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Avoid duplicate reports
        existing = GeneratedReport.objects.filter(
            user=request.user, period=period,
            period_start=period_start, period_end=period_end, status='ready',
        ).first()
        if existing:
            return Response({
                'message': 'Report already exists.',
                'report': GeneratedReportSerializer(existing).data,
            })

        report = GeneratedReport.objects.create(
            user=request.user,
            period=period,
            period_start=period_start,
            period_end=period_end,
            status='pending',
        )

        try:
            report_data = aggregate_report_data(request.user, period_start, period_end)
            ai_summary = generate_ai_analysis(
                report_data, period, str(period_start), str(period_end)
            )
            pdf_bytes = generate_pdf(
                report_data, ai_summary, period, str(period_start), str(period_end)
            )

            filename = f"report_{request.user.id}_{period}_{period_start}.pdf"
            report.pdf_file.save(filename, ContentFile(pdf_bytes), save=False)
            report.ai_summary = ai_summary
            report.status = 'ready'
            report.save()

        except Exception as e:
            logger.exception(f"Report generation failed for user {request.user.id}: {e}")
            report.status = 'failed'
            report.save()
            return Response(
                {'error': 'Report generation failed. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {'message': 'Report generated successfully.', 'report': GeneratedReportSerializer(report).data},
            status=status.HTTP_201_CREATED,
        )


class DownloadReportView(APIView):
    """GET /api/reports/<id>/download/ — stream PDF to client."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report = GeneratedReport.objects.get(pk=pk, user=request.user, status='ready')
        except GeneratedReport.DoesNotExist:
            return Response({'error': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

        if not report.pdf_file:
            return Response({'error': 'PDF file missing.'}, status=status.HTTP_404_NOT_FOUND)

        filename = f"FitnessAI_{report.period}_{report.period_start}_{report.period_end}.pdf"
        response = HttpResponse(report.pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class SendReportEmailView(APIView):
    """POST /api/reports/<id>/send-email/ — email the PDF to user or custom address."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            report = GeneratedReport.objects.get(pk=pk, user=request.user, status='ready')
        except GeneratedReport.DoesNotExist:
            return Response({'error': 'Report not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SendReportEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_email = serializer.validated_data.get('email') or request.user.email

        if not report.pdf_file:
            return Response({'error': 'PDF file not available.'}, status=status.HTTP_400_BAD_REQUEST)

        pdf_bytes = report.pdf_file.read()
        user_name = request.user.get_full_name() or request.user.email.split('@')[0]

        sent = send_report_email(
            to_email=target_email,
            user_name=user_name,
            period=report.period,
            period_start=str(report.period_start),
            period_end=str(report.period_end),
            pdf_bytes=pdf_bytes,
            report_id=report.id,
        )

        if not sent:
            return Response({'error': 'Failed to send email.'}, status=status.HTTP_502_BAD_GATEWAY)

        report.email_sent = True
        report.email_sent_at = timezone.now()
        report.save(update_fields=['email_sent', 'email_sent_at'])

        return Response({'message': f'Report sent to {target_email} successfully.'})


class ReportListView(APIView):
    """GET /api/reports/ — list all user reports."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reports = GeneratedReport.objects.filter(user=request.user).order_by('-created_at')
        return Response(GeneratedReportSerializer(reports, many=True).data)


class ReportDetailView(APIView):
    """GET /api/reports/<id>/ — fetch a single report with full AI summary."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            report = GeneratedReport.objects.get(pk=pk, user=request.user)
        except GeneratedReport.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GeneratedReportSerializer(report).data)

    def delete(self, request, pk):
        try:
            report = GeneratedReport.objects.get(pk=pk, user=request.user)
        except GeneratedReport.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        if report.pdf_file:
            report.pdf_file.delete(save=False)
        report.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
