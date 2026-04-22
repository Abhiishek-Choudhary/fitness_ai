from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fitness_ai.throttles import AIEndpointUserThrottle, AIEndpointAnonThrottle
from workout_agent.agents.exercise_enricher import enrich_workout_plan


class EnrichedWorkoutAPIView(APIView):
    throttle_classes = [AIEndpointUserThrottle, AIEndpointAnonThrottle]

    def post(self, request):
        body = request.data
        if not body:
            return Response({"error": "Invalid or empty JSON body"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            enriched_plan = enrich_workout_plan(body)
            return Response(enriched_plan, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
