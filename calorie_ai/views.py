import tempfile
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from fitness_ai.throttles import AIEndpointUserThrottle, AIEndpointAnonThrottle
from .models import FoodLog
from .serializers import FoodImageSerializer, FoodLogSerializer, FoodLogCreateFromEstimateSerializer
from .services.gemini_client import analyze_food_image
from .services.calorie_mapper import estimate_calories


class CalorieEstimateView(APIView):
    throttle_classes = [AIEndpointUserThrottle, AIEndpointAnonThrottle]

    def post(self, request):
        serializer = FoodImageSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image = serializer.validated_data["image"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp:
            for chunk in image.chunks():
                temp.write(chunk)
            image_path = temp.name

        try:
            ai_result = analyze_food_image(image_path)
            total, breakdown = estimate_calories(ai_result["items"])
            return Response({
                "total_calories": total,
                "items": breakdown,
                "confidence": 0.75,
                "note": "Calories are estimated using AI",
            })
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FoodLogCreateView(APIView):
    """POST /api/calories/log/ — manually log a food entry."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FoodLogSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class FoodLogFromEstimateView(APIView):
    """POST /api/calories/log/bulk/ — save AI estimate results directly as food log entries."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = FoodLogCreateFromEstimateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        logs = []
        for item in data['items']:
            log = FoodLog.objects.create(
                user=request.user,
                food_name=item.get('name', 'Unknown'),
                meal_type=data['meal_type'],
                calories=item.get('calories', 0),
                quantity_description=str(item.get('quantity', '')),
                logged_on=data['logged_on'],
            )
            logs.append(log)

        return Response(FoodLogSerializer(logs, many=True).data, status=status.HTTP_201_CREATED)


class FoodLogListView(APIView):
    """GET /api/calories/log/?date=YYYY-MM-DD — list food logs for a date."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date = request.query_params.get('date', timezone.now().date())
        logs = FoodLog.objects.filter(user=request.user, logged_on=date)
        total = sum(l.calories for l in logs)
        return Response({
            'date': date,
            'total_calories': round(total, 1),
            'logs': FoodLogSerializer(logs, many=True).data,
        })


class FoodLogDeleteView(APIView):
    """DELETE /api/calories/log/<pk>/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            log = FoodLog.objects.get(pk=pk, user=request.user)
        except FoodLog.DoesNotExist:
            return Response({'error': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)
        log.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
