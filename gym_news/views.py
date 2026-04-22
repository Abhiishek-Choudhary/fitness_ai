from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .services.news_fetcher import fetch_news, fetch_all_categories, CATEGORY_QUERIES


class GymNewsListView(APIView):
    """
    GET /api/news/
    Returns top news across all categories (5 articles each).

    GET /api/news/?category=hyrox
    Returns paginated news for a specific category.

    Query params:
        category  — hyrox | ironman | olympia | crossfit | powerlifting | fitness
        page      — page number (default 1)
        page_size — results per page, max 20 (default 10)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        category = request.query_params.get("category", "").strip().lower()
        page = self._parse_int(request.query_params.get("page", "1"), default=1, minimum=1)
        page_size = self._parse_int(request.query_params.get("page_size", "10"), default=10, minimum=1, maximum=20)

        if not category:
            data = fetch_all_categories(page_size=5)
            return Response({
                "available_categories": list(CATEGORY_QUERIES.keys()),
                "news": data,
            }, status=status.HTTP_200_OK)

        data = fetch_news(category=category, page=page, page_size=page_size)

        if "error" in data and not data.get("articles"):
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)

    def _parse_int(self, value, default, minimum=1, maximum=None):
        try:
            result = int(value)
            result = max(result, minimum)
            if maximum:
                result = min(result, maximum)
            return result
        except (ValueError, TypeError):
            return default


class GymNewsCategoryView(APIView):
    """
    GET /api/news/<category>/
    Shorthand category-specific endpoint.
    e.g. /api/news/hyrox/  /api/news/ironman/  /api/news/olympia/

    Query params:
        page      — page number (default 1)
        page_size — results per page, max 20 (default 10)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, category):
        category = category.strip().lower()
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 10)), 20)

        data = fetch_news(category=category, page=page, page_size=page_size)

        if "error" in data and not data.get("articles"):
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

        return Response(data, status=status.HTTP_200_OK)


class GymNewsCategoriesView(APIView):
    """
    GET /api/news/categories/
    Returns all available news categories.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "categories": list(CATEGORY_QUERIES.keys()),
            "description": {
                "hyrox": "Hyrox race events, results, and upcoming competitions",
                "ironman": "Ironman triathlon events, results, and upcoming races",
                "olympia": "Mr. Olympia, bodybuilding competitions and results",
                "crossfit": "CrossFit Games, Open, and competition news",
                "powerlifting": "Powerlifting world records and competition news",
                "fitness": "General gym, fitness, and training news",
            }
        }, status=status.HTTP_200_OK)
