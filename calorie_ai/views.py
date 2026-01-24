import tempfile
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import FoodImageSerializer
from .services.gemini_client import analyze_food_image
from .services.calorie_mapper import estimate_calories

class CalorieEstimateView(APIView):
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
                "note": "Calories are estimated using AI"
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
