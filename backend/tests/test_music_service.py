import io
import json
import os
import sys
import urllib.error
import urllib.parse

import pytest

# The backend imports modules as "services.*", so make backend/ importable
# no matter which directory pytest is started from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import services.music_service as music_service  # noqa: E402
from services.music_service import EMOTION_QUERIES, get_song_by_emotion  # noqa: E402

NO_SONG = {"name": "No song found", "artist": "", "url": "", "track_id": ""}

FAKE_TRACK = {
    "id": 12345,
    "title": "Test Song",
    "artist": {"name": "Test Artist"},
    "link": "https://www.deezer.com/track/12345",
}


class FakeDeezer:
    """Stands in for urllib.request.urlopen and records the queries sent."""

    def __init__(self, payload=None, exc=None):
        self.payload = payload
        self.exc = exc
        self.queries = []

    def __call__(self, req, timeout=None):
        url = req.full_url if hasattr(req, "full_url") else req
        params = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.queries.append(params["q"][0])
        if self.exc:
            raise self.exc
        return io.BytesIO(json.dumps(self.payload).encode("utf-8"))


@pytest.fixture(autouse=True)
def clear_recent_tracks():
    music_service._recent_track_ids.clear()
    yield
    music_service._recent_track_ids.clear()


def use_fake(monkeypatch, **kwargs):
    fake = FakeDeezer(**kwargs)
    monkeypatch.setattr(music_service.urllib.request, "urlopen", fake)
    return fake


def test_valid_emotion_returns_song_fields(monkeypatch):
    fake = use_fake(monkeypatch, payload={"data": [FAKE_TRACK], "total": 1})

    song = get_song_by_emotion("happy")

    assert song == {
        "name": "Test Song",
        "artist": "Test Artist",
        "url": "https://www.deezer.com/track/12345",
        "track_id": "12345",
    }
    assert isinstance(song["track_id"], str)
    assert fake.queries and all(q in EMOTION_QUERIES["happy"] for q in fake.queries)


def test_unknown_emotion_falls_back_to_neutral(monkeypatch):
    fake = use_fake(monkeypatch, payload={"data": [FAKE_TRACK], "total": 1})

    song = get_song_by_emotion("confused")

    assert song["name"] == "Test Song"
    assert fake.queries and all(q in EMOTION_QUERIES["neutral"] for q in fake.queries)


def test_deezer_error_in_response_returns_no_song(monkeypatch):
    # Deezer reports errors inside a normal 200 response body
    use_fake(monkeypatch, payload={"error": {"type": "Exception", "message": "Quota limit exceeded", "code": 4}})

    assert get_song_by_emotion("sad") == NO_SONG


def test_network_failure_returns_no_song(monkeypatch):
    use_fake(monkeypatch, exc=urllib.error.URLError("connection refused"))

    assert get_song_by_emotion("angry") == NO_SONG
