from rest_framework import serializers
from .models import GeneratedReport
import datetime


class GenerateReportSerializer(serializers.Serializer):
    PERIOD_CHOICES = ['weekly', 'monthly']
    period = serializers.ChoiceField(choices=PERIOD_CHOICES)
    year = serializers.IntegerField(min_value=2020, max_value=2100)
    month = serializers.IntegerField(min_value=1, max_value=12, required=False)
    week = serializers.IntegerField(min_value=1, max_value=53, required=False)

    def validate(self, data):
        if data['period'] == 'monthly' and not data.get('month'):
            raise serializers.ValidationError("'month' is required for monthly reports.")
        if data['period'] == 'weekly' and not data.get('week'):
            raise serializers.ValidationError("'week' is required for weekly reports (ISO week number).")
        return data


class GeneratedReportSerializer(serializers.ModelSerializer):
    pdf_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedReport
        fields = [
            'id', 'period', 'period_start', 'period_end', 'status',
            'ai_summary', 'pdf_url', 'download_url',
            'email_sent', 'email_sent_at', 'created_at',
        ]

    def get_pdf_url(self, obj):
        if obj.pdf_file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.pdf_file.url)
            return obj.pdf_file.url
        return None

    def get_download_url(self, obj):
        return f"/api/reports/{obj.id}/download/"


class SendReportEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=False,
        help_text="Optional override email. Defaults to the authenticated user's email.",
    )
