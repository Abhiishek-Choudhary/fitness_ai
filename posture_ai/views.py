from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from fitness_ai.throttles import AIEndpointUserThrottle, AIEndpointAnonThrottle
from .models import PostureSession, PostureImage
from .serializers import PostureSessionSerializer


class PushUpImageUploadAPI(APIView):
    throttle_classes = [AIEndpointUserThrottle, AIEndpointAnonThrottle]

    def post(self, request):
        images = request.FILES.getlist("images")

        if len(images) < 3:
            return Response(
                {"error": "Upload at least 3 images"},
                status=status.HTTP_400_BAD_REQUEST
            )

        session = PostureSession.objects.create(
            exercise_type="push_up"
        )

        for img in images:
            PostureImage.objects.create(
                session=session,
                image=img
            )

        serializer = PostureSessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from .models import PostureSession
from .services.posture_analyzer import analyze_pushup
from .services.feedback_generator import generate_feedback


class AnalyzePostureAPIView(APIView):
    throttle_classes = [AIEndpointUserThrottle, AIEndpointAnonThrottle]

    def post(self, request, session_id):
        try:
            session = PostureSession.objects.get(id=session_id)
        except PostureSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)

        # Temporary mocked metrics (later replaced by ML)
        metrics = {
            "elbow_angle": 128,
            "body_angle_deviation": 14
        }

        analysis = analyze_pushup(metrics)

        feedback = generate_feedback(
            exercise=session.exercise_type,
            score=analysis["score"],
            issues=analysis["issues"],
            metrics=metrics
        )

        session.final_score = analysis["score"]
        session.is_correct = analysis["is_correct"]
        session.feedback = {
            "issues": analysis["issues"],
            "ai_feedback": feedback
        }
        session.save()

        return Response({
            "session_id": session.id,
            "score": session.final_score,
            "is_correct": session.is_correct,
            "feedback": session.feedback
        })
