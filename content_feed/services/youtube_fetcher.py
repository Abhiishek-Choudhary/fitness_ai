"""
YouTube Data API v3 client — Single Responsibility: fetch video metadata.
No Django imports; pure HTTP + data mapping.
"""
import requests
from typing import Optional

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

# Seed catalogue: (query, fitness_category, difficulty, content_type, count)
SEED_CATALOGUE = [
    ("weight loss cardio workout home",      "weight_loss",  "beginner",     "video",           6),
    ("fat burning HIIT workout no equipment","hiit",         "intermediate", "video",           5),
    ("muscle building strength training",    "muscle_gain",  "intermediate", "video",           6),
    ("yoga for flexibility beginners",       "yoga",         "beginner",     "exercise_guide",  5),
    ("advanced strength powerlifting tips",  "strength",     "advanced",     "exercise_guide",  4),
    ("healthy meal prep nutrition fitness",  "nutrition",    "beginner",     "nutrition_tip",   5),
    ("running cardio endurance training",    "cardio",       "intermediate", "video",           5),
    ("stretching recovery exercises daily",  "flexibility",  "beginner",     "exercise_guide",  4),
    ("HIIT advanced workout challenge",      "hiit",         "advanced",     "video",           4),
    ("bodyweight workout muscle gain",       "muscle_gain",  "beginner",     "video",           4),
]


def _thumbnail(snippet: dict) -> str:
    thumbs = snippet.get('thumbnails', {})
    for key in ('maxres', 'high', 'medium', 'default'):
        if key in thumbs:
            return thumbs[key].get('url', '')
    return ''


def search_videos(api_key: str, query: str, max_results: int = 5) -> list[dict]:
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results,
        'key': api_key,
        'relevanceLanguage': 'en',
        'safeSearch': 'strict',
    }
    try:
        resp = requests.get(YOUTUBE_SEARCH_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get('items', [])
    except Exception as e:
        print(f"  [YouTube] Search failed for '{query}': {e}")
        return []

    results = []
    for item in items:
        video_id = item.get('id', {}).get('videoId')
        if not video_id:
            continue
        snippet = item.get('snippet', {})
        results.append({
            'youtube_video_id': video_id,
            'title': snippet.get('title', ''),
            'body': snippet.get('description', '')[:500],
            'thumbnail_url': _thumbnail(snippet),
            'channel_title': snippet.get('channelTitle', ''),
        })
    return results


def fetch_video_duration(api_key: str, video_ids: list[str]) -> dict[str, Optional[int]]:
    """Return {video_id: duration_seconds} using the videos.list endpoint."""
    if not video_ids:
        return {}
    params = {
        'part': 'contentDetails',
        'id': ','.join(video_ids),
        'key': api_key,
    }
    try:
        resp = requests.get(YOUTUBE_VIDEOS_URL, params=params, timeout=10)
        resp.raise_for_status()
        items = resp.json().get('items', [])
    except Exception:
        return {}

    durations = {}
    import re
    for item in items:
        vid_id = item['id']
        iso = item.get('contentDetails', {}).get('duration', '')
        # Parse ISO 8601 duration e.g. PT12M34S
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', iso)
        if match:
            h, m, s = (int(x or 0) for x in match.groups())
            durations[vid_id] = h * 3600 + m * 60 + s
        else:
            durations[vid_id] = None
    return durations
