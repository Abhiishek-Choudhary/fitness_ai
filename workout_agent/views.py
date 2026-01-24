from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from workout_agent.agents.exercise_enricher import enrich_workout_plan

@csrf_exempt
def enriched_workout_api(request):
    """
    POST endpoint:
    Input: JSON from Gemini AI (raw workout plan)
    Output: JSON enriched with videos
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    try:
        enriched_plan = enrich_workout_plan(body)
        return JsonResponse(enriched_plan, safe=False, status=200)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
