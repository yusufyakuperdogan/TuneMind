import os
import sys
import types

import pytest
from fastapi.testclient import TestClient

# The backend imports modules as "services.*", so make backend/ importable
# no matter which directory pytest is started from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# services.emotion_service loads the Hugging Face model when it is imported.
# If it isn't loaded yet, put a stand-in in place just while importing the app,
# then remove it so other test files still get the real module.
_real_emotion_service = sys.modules.get("services.emotion_service")
if _real_emotion_service is None:
    _stub = types.ModuleType("services.emotion_service")
    _stub.detect_emotion = lambda text: pytest.fail("detect_emotion was not mocked")
    sys.modules["services.emotion_service"] = _stub
try:
    import routes.emotion_routes as emotion_routes  # noqa: E402
    from main import app  # noqa: E402
finally:
    if _real_emotion_service is None:
        sys.modules.pop("services.emotion_service", None)

PLAYLIST_SONG = {
    "name": "Playlist Song",
    "artist": "Playlist Artist",
    "url": "https://www.deezer.com/track/111",
    "track_id": "111",
}
SEARCH_SONG = {
    "name": "Search Song",
    "artist": "Search Artist",
    "url": "https://www.deezer.com/track/222",
    "track_id": "222",
}
NO_SONG = {"name": "No song found", "artist": "", "url": "", "track_id": ""}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def calls(monkeypatch):
    """Mock all services and record how they were called.

    Set calls["playlist_result"] / calls["search_result"] in a test to change
    what the fake music functions return.
    """
    recorded = {
        "detect_emotion": [],
        "get_song_from_playlist": [],
        "get_song_by_emotion": [],
        "playlist_result": PLAYLIST_SONG,
        "search_result": SEARCH_SONG,
    }

    def fake_detect_emotion(text):
        recorded["detect_emotion"].append(text)
        return "happy"

    def fake_get_song_from_playlist(emotion):
        recorded["get_song_from_playlist"].append(emotion)
        return dict(recorded["playlist_result"])

    def fake_get_song_by_emotion(emotion):
        recorded["get_song_by_emotion"].append(emotion)
        return dict(recorded["search_result"])

    monkeypatch.setattr(emotion_routes, "detect_emotion", fake_detect_emotion)
    monkeypatch.setattr(emotion_routes, "get_song_from_playlist", fake_get_song_from_playlist)
    monkeypatch.setattr(emotion_routes, "get_song_by_emotion", fake_get_song_by_emotion)
    return recorded


def test_post_emotion_returns_playlist_song(client, calls):
    response = client.post("/emotion/", json={"text": "I feel great today!"})

    assert response.status_code == 200
    assert response.json() == {
        "text": "I feel great today!",
        "emotion": "happy",
        "song": PLAYLIST_SONG,
    }
    assert calls["detect_emotion"] == ["I feel great today!"]
    assert calls["get_song_from_playlist"] == ["happy"]
    assert calls["get_song_by_emotion"] == []  # no fallback needed


def test_post_emotion_falls_back_to_search_when_playlist_has_no_song(client, calls):
    calls["playlist_result"] = NO_SONG

    response = client.post("/emotion/", json={"text": "I feel great today!"})

    assert response.status_code == 200
    assert response.json()["song"] == SEARCH_SONG
    assert calls["get_song_from_playlist"] == ["happy"]
    assert calls["get_song_by_emotion"] == ["happy"]


def test_post_emotion_returns_no_song_when_both_fail(client, calls):
    calls["playlist_result"] = NO_SONG
    calls["search_result"] = NO_SONG

    response = client.post("/emotion/", json={"text": "I feel great today!"})

    assert response.status_code == 200
    assert response.json()["song"] == NO_SONG


def test_post_emotion_without_text_returns_422(client, calls):
    response = client.post("/emotion/", json={})

    assert response.status_code == 422
    assert any(err["loc"][-1] == "text" for err in response.json()["detail"])
    assert calls["detect_emotion"] == []
    assert calls["get_song_from_playlist"] == []
    assert calls["get_song_by_emotion"] == []
