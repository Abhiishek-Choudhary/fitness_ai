from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination

from .models import Workout, WorkoutSession
from .serializers import WorkoutSerializer, WorkoutSessionSerializer


# List all workouts
class WorkoutListView(generics.ListAPIView):
    queryset = Workout.objects.all()
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination


# Log a workout session
class WorkoutSessionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = WorkoutSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data)


# List user workout sessions
class WorkoutSessionListView(generics.ListAPIView):
    serializer_class = WorkoutSessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        return WorkoutSession.objects.filter(user=self.request.user).order_by('-date')
