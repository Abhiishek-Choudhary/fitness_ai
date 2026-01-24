import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
from workout_agent.agents.exercise_processor import normalize_exercise_name

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Simple in-memory cache
video_cache = {}

def search_exercise_video(exercise_name, max_results=1):
    """
    Search YouTube for exercise tutorial videos.
    Returns top 'max_results' videos with title, URL, channel.
    Uses cache to avoid repeated API calls.
    """
    # Normalize exercise for cache key
    key = exercise_name.lower()
    if key in video_cache:
        return video_cache[key]

    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_API_KEY)

    query = f"{normalize_exercise_name(exercise_name)} exercise tutorial"

    request = youtube.search().list(
        q=query,
        part="snippet",
        maxResults=max_results,
        type="video",
        videoDuration="short"  # short or medium videos
    )
    response = request.execute()

    results = []
    for item in response.get("items", []):
        results.append({
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            "channel": item["snippet"]["channelTitle"]
        })

    # Cache results
    video_cache[key] = results

    return results
