import json
import random
import threading
import urllib.parse
import urllib.request
from collections import deque

DEEZER_SEARCH_URL = "https://api.deezer.com/search"

# Track IDs returned most recently (shared across all emotions), so the same
# song isn't suggested again right away. In-memory only: resets on restart.
RECENT_LIMIT = 20
_recent_track_ids = deque(maxlen=RECENT_LIMIT)
_recent_lock = threading.Lock()

EMOTION_QUERIES = {
    "happy": [
        "happy upbeat pop",
        "feel good summer hits",
        "energetic dance music",
        "positive vibes",
        "uplifting indie pop"
    ],
    "sad": [
        "sad emotional acoustic",
        "heartbreak ballad",
        "melancholic indie",
        "sad piano",
        "lonely night"
    ],
    "angry": [
        "heavy metal rage",
        "intense workout",
        "aggressive hip hop",
        "hard rock energy",
        "punk rock rage"
    ],
    "neutral": [
        "chill ambient relaxing",
        "lofi hip hop study",
        "popular hits",
        "indie pop mix",
        "soft jazz evening"
    ]
}

NO_SONG = {"name": "No song found", "artist": "", "url": "", "track_id": ""}


def _search_deezer(query: str, index: int = 0, limit: int = 10) -> list:
    params = urllib.parse.urlencode({"q": query, "index": index, "limit": limit})
    req = urllib.request.Request(
        f"{DEEZER_SEARCH_URL}?{params}",
        headers={"User-Agent": "TuneMind/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    # Deezer reports errors inside a 200 response body
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return payload.get("data", [])


def get_song_by_emotion(emotion: str) -> dict:
    queries = EMOTION_QUERIES.get((emotion or "").lower(), EMOTION_QUERIES["neutral"])
    query = random.choice(queries)
    index = random.randint(0, 40)

    try:
        tracks = _search_deezer(query, index=index)
        # A random offset can overshoot the result count; retry from the start
        if not tracks and index > 0:
            tracks = _search_deezer(query, index=0)
    except Exception as e:
        print("Deezer API Error:", e)
        return dict(NO_SONG)

    if not tracks:
        return dict(NO_SONG)

    with _recent_lock:
        fresh = [t for t in tracks if str(t.get("id", "")) not in _recent_track_ids]
        # If every result was returned recently, fall back to any of them
        track = random.choice(fresh or tracks)
        _recent_track_ids.append(str(track.get("id", "")))

    return {
        "name": track.get("title", ""),
        "artist": track.get("artist", {}).get("name", ""),
        "url": track.get("link", ""),
        "track_id": str(track.get("id", ""))
    }
