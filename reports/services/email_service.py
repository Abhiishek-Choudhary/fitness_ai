"""Send fitness report as email attachment."""
import os
from django.core.mail import EmailMessage
from django.conf import settings


def send_report_email(to_email: str, user_name: str, period: str,
                      period_start: str, period_end: str,
                      pdf_bytes: bytes, report_id: int) -> bool:
    subject = f"Your FitnessAI {period.title()} Report — {period_start} to {period_end}"

    body = f"""Hi {user_name},

Your {period} fitness report is ready! 🏋️

Period: {period_start} to {period_end}

Attached is your detailed performance report including:
  • Workout sessions & calorie burn analysis
  • Nutrition & food intake breakdown
  • Body progress tracking
  • Personalised AI coach recommendations

Keep pushing — every session counts!

— The FitnessAI Team

---
This report was generated automatically. Do not reply to this email.
"""

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[to_email],
    )
    filename = f"FitnessAI_{period}_report_{period_start}_{period_end}.pdf"
    email.attach(filename, pdf_bytes, 'application/pdf')

    try:
        email.send(fail_silently=False)
        return True
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Report email failed for {to_email}: {e}")
        return False
