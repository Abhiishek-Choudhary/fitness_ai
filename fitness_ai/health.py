from django.http import JsonResponse


def healthz(request):
    """Liveness probe.

    Plain Django rather than DRF on purpose: the DRF anon throttle is 100/day,
    which a keep-alive pinger hitting this every 10 minutes would blow through.
    Deliberately shallow — it reports that the process is serving, nothing more,
    so a transient database blip cannot fail Render's health check and trigger a
    restart loop.
    """
    return JsonResponse({'status': 'ok'})
