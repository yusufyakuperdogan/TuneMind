import json
import random
import threading
import urllib.parse
import urllib.request
from collections import deque

DEEZER_API_URL = "https://api.deezer.com"

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
    "relaxed": [
        "peaceful piano",
        "relaxing guitar",
        "chill acoustic",
        "cozy coffee jazz",
        "sunday morning chill"
    ],
    "neutral": [
        "chill ambient relaxing",
        "lofi hip hop study",
        "popular hits",
        "indie pop mix",
        "soft jazz evening"
    ]
}

# Mood terms for searching curated Deezer playlists (2-3 per emotion)
PLAYLIST_QUERIES = {
    "happy": ["happy hits", "feel good", "good vibes"],
    "sad": ["sad songs", "heartbreak"],
    "angry": ["rage", "metal workout", "hard rock"],
    "relaxed": ["chill vibes", "calm piano", "relaxing acoustic"],
    "neutral": ["lofi", "indie pop"]
}
MIN_PLAYLIST_TRACKS = 30
# Only the best-matching playlists are considered; lower results drift off-theme
PLAYLIST_CANDIDATES = 10
PLAYLIST_TRACKS_PAGE = 50

NO_SONG = {"name": "No song found", "artist": "", "url": "", "track_id": ""}


def _deezer_get(path: str, params: dict) -> dict:
    query = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        f"{DEEZER_API_URL}/{path}?{query}",
        headers={"User-Agent": "TuneMind/1.0"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    # Deezer reports errors inside a 200 response body
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return payload


def _search_deezer(query: str, index: int = 0, limit: int = 10) -> list:
    payload = _deezer_get("search", {"q": query, "index": index, "limit": limit})
    return payload.get("data", [])


def _pick_fresh_track(tracks: list) -> dict:
    """Pick a random track, avoiding recently returned ones, and remember it."""
    with _recent_lock:
        fresh = [t for t in tracks if str(t.get("id", "")) not in _recent_track_ids]
        # If every result was returned recently, fall back to any of them
        track = random.choice(fresh or tracks)
        _recent_track_ids.append(str(track.get("id", "")))
    return track


def _to_song(track: dict) -> dict:
    return {
        "name": track.get("title", ""),
        "artist": track.get("artist", {}).get("name", ""),
        "url": track.get("link", ""),
        "track_id": str(track.get("id", ""))
    }


def _find_playlist(emotion: str) -> dict | None:
    """Search Deezer for a curated playlist matching the emotion's mood."""
    terms = PLAYLIST_QUERIES.get((emotion or "").lower(), PLAYLIST_QUERIES["neutral"])
    term = random.choice(terms)
    payload = _deezer_get("search/playlist", {"q": term, "limit": PLAYLIST_CANDIDATES})
    playlists = [
        p for p in payload.get("data", [])
        if p.get("nb_tracks", 0) >= MIN_PLAYLIST_TRACKS
    ]
    return random.choice(playlists) if playlists else None


def _get_playlist_song(emotion: str) -> tuple[dict, dict | None]:
    """Return (song, playlist) so callers can see which playlist was used."""
    try:
        playlist = _find_playlist(emotion)
        if playlist is None:
            return dict(NO_SONG), None

        # Start at a random spot so long playlists don't always give the first songs
        max_index = max(0, playlist["nb_tracks"] - PLAYLIST_TRACKS_PAGE)
        index = random.randint(0, max_index)
        payload = _deezer_get(
            f"playlist/{playlist['id']}/tracks",
            {"index": index, "limit": PLAYLIST_TRACKS_PAGE}
        )
        # Skip tracks that can't be played in this region
        tracks = [t for t in payload.get("data", []) if t.get("readable", True)]
    except Exception as e:
        print("Deezer API Error:", e)
        return dict(NO_SONG), None

    if not tracks:
        return dict(NO_SONG), playlist

    return _to_song(_pick_fresh_track(tracks)), playlist


def get_song_from_playlist(emotion: str) -> dict:
    """Like get_song_by_emotion, but picks from a curated Deezer playlist."""
    song, _ = _get_playlist_song(emotion)
    return song


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

    return _to_song(_pick_fresh_track(tracks))
