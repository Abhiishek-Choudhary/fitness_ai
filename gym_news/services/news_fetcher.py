import requests
from django.core.cache import cache
from django.conf import settings

NEWS_API_BASE = "https://newsapi.org/v2/everything"

# Search queries per category — tuned for fitness/competition news
CATEGORY_QUERIES = {
    "hyrox": (
        "Hyrox race OR Hyrox event OR Hyrox winner OR Hyrox champion "
        "OR Hyrox 2024 OR Hyrox 2025 OR Hyrox results"
    ),
    "ironman": (
        "Ironman triathlon OR Ironman race OR Ironman event OR Ironman winner "
        "OR Ironman champion OR Ironman results OR Ironman 2025"
    ),
    "olympia": (
        "Mr Olympia OR Olympia bodybuilding OR Olympia winner OR Olympia champion "
        "OR Olympia 2025 OR Men's Physique Olympia OR Classic Physique Olympia"
    ),
    "crossfit": (
        "CrossFit Games OR CrossFit competition OR CrossFit Open OR CrossFit winner "
        "OR CrossFit champion 2025"
    ),
    "powerlifting": (
        "powerlifting world record OR IPF powerlifting OR powerlifting champion "
        "OR powerlifting competition 2025"
    ),
    "fitness": (
        "gym fitness bodybuilding workout training OR strength training news "
        "OR fitness competition 2025"
    ),
}

CACHE_TIMEOUT = 60 * 60  # 1 hour


def fetch_news(category: str = "fitness", page: int = 1, page_size: int = 10) -> dict:
    """
    Fetch gym/competition news for a given category.
    Results are cached for 1 hour to avoid burning API quota.
    """
    category = category.lower()
    if category not in CATEGORY_QUERIES:
        available = list(CATEGORY_QUERIES.keys())
        return {
            "error": f"Invalid category '{category}'. Available: {available}",
            "articles": [],
            "total_results": 0,
        }

    cache_key = f"gym_news_{category}_page{page}_size{page_size}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    api_key = getattr(settings, "NEWS_API_KEY", None)
    if not api_key:
        return {
            "error": "NEWS_API_KEY not configured in settings.",
            "articles": [],
            "total_results": 0,
        }

    params = {
        "q": CATEGORY_QUERIES[category],
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "page": page,
        "apiKey": api_key,
    }

    try:
        response = requests.get(NEWS_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.Timeout:
        return {"error": "News API request timed out.", "articles": [], "total_results": 0}
    except requests.exceptions.RequestException as e:
        return {"error": f"News API request failed: {str(e)}", "articles": [], "total_results": 0}

    if data.get("status") != "ok":
        return {
            "error": data.get("message", "Unknown error from News API"),
            "articles": [],
            "total_results": 0,
        }

    articles = [_format_article(a) for a in data.get("articles", [])]

    result = {
        "category": category,
        "total_results": data.get("totalResults", 0),
        "page": page,
        "page_size": page_size,
        "articles": articles,
    }

    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def fetch_all_categories(page_size: int = 5) -> dict:
    """Fetch top headlines across all categories in one call."""
    result = {}
    for category in CATEGORY_QUERIES:
        data = fetch_news(category=category, page=1, page_size=page_size)
        result[category] = {
            "total_results": data.get("total_results", 0),
            "articles": data.get("articles", []),
        }
    return result


def _format_article(article: dict) -> dict:
    """Normalise a raw NewsAPI article into a clean response shape."""
    source = article.get("source") or {}
    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "content": article.get("content"),
        "url": article.get("url"),
        "image_url": article.get("urlToImage"),
        "published_at": article.get("publishedAt"),
        "source": source.get("name"),
        "author": article.get("author"),
    }
