from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from django.core.exceptions import ValidationError
from django.utils import timezone

from dashboard.services.progress_service import (
    create_or_update_progress_entry,
    delete_progress_entry,
    get_user_progress_entries,
)
from dashboard.serializers import (
    ProgressEntryCreateSerializer,
    ProgressEntryListSerializer,
)


class ProgressEntryCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ProgressEntryCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        # Pass correct field names to service
        entry = create_or_update_progress_entry(
            user=request.user,
            recorded_on=data.get("recorded_on") or timezone.now().date(),
            weight=data.get("weight"),
            note=data.get("note"),
            images_data=[{"image": data.get("image"), "image_type": "front"}],
        )

        return Response(
            {"id": entry.id, "message": "Progress saved successfully"},
            status=status.HTTP_201_CREATED,
        )


class ProgressEntryListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = get_user_progress_entries(user=request.user)
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = ProgressEntryListSerializer(page, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)


class ProgressEntryDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            delete_progress_entry(user=request.user, entry_id=pk)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {"message": "Progress entry deleted"},
            status=status.HTTP_204_NO_CONTENT,
        )
