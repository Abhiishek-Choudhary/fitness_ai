from django.contrib import admin
from .models import GeneratedReport


@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
    list_display = ['user', 'period', 'period_start', 'period_end', 'status', 'email_sent', 'created_at']
    list_filter = ['period', 'status', 'email_sent']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'ai_summary', 'pdf_file']
