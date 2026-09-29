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
from services.music_service import (  # noqa: E402
    EMOTION_QUERIES,
    PLAYLIST_QUERIES,
    get_song_by_emotion,
    get_song_from_playlist,
)

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


# --- get_song_from_playlist ---------------------------------------------------


def make_playlist(playlist_id, nb_tracks):
    return {"id": playlist_id, "title": f"Playlist {playlist_id}", "nb_tracks": nb_tracks}


class FakePlaylistDeezer:
    """Stands in for urllib.request.urlopen and answers by API path.

    search/playlist      -> playlist_payload
    playlist/{id}/tracks -> tracks_payload
    """

    def __init__(self, playlist_payload=None, tracks_payload=None, exc=None):
        self.playlist_payload = playlist_payload
        self.tracks_payload = tracks_payload if tracks_payload is not None else {"data": [FAKE_TRACK]}
        self.exc = exc
        self.requests = []  # (path, params) for every call

    def __call__(self, req, timeout=None):
        url = urllib.parse.urlparse(req.full_url if hasattr(req, "full_url") else req)
        path = url.path.lstrip("/")
        params = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        self.requests.append((path, params))
        if self.exc:
            raise self.exc
        if path == "search/playlist":
            payload = self.playlist_payload
        elif path.startswith("playlist/") and path.endswith("/tracks"):
            payload = self.tracks_payload
        else:
            raise AssertionError(f"unexpected Deezer path: {path}")
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    def search_terms(self):
        return [p["q"] for path, p in self.requests if path == "search/playlist"]

    def fetched_playlists(self):
        return [path.split("/")[1] for path, _ in self.requests if path.endswith("/tracks")]


def use_playlist_fake(monkeypatch, **kwargs):
    fake = FakePlaylistDeezer(**kwargs)
    monkeypatch.setattr(music_service.urllib.request, "urlopen", fake)
    return fake


def test_playlist_song_returns_song_fields(monkeypatch):
    fake = use_playlist_fake(monkeypatch, playlist_payload={"data": [make_playlist(111, 50)]})

    song = get_song_from_playlist("happy")

    assert song == {
        "name": "Test Song",
        "artist": "Test Artist",
        "url": "https://www.deezer.com/track/12345",
        "track_id": "12345",
    }
    assert fake.search_terms() and all(t in PLAYLIST_QUERIES["happy"] for t in fake.search_terms())
    assert fake.fetched_playlists() == ["111"]


def test_playlist_unknown_emotion_falls_back_to_neutral(monkeypatch):
    fake = use_playlist_fake(monkeypatch, playlist_payload={"data": [make_playlist(111, 50)]})

    song = get_song_from_playlist("confused")

    assert song["name"] == "Test Song"
    assert fake.search_terms() and all(t in PLAYLIST_QUERIES["neutral"] for t in fake.search_terms())


def test_playlist_with_fewer_than_30_tracks_is_skipped(monkeypatch):
    playlists = [make_playlist(1, 29), make_playlist(2, 30), make_playlist(3, 5)]
    fake = use_playlist_fake(monkeypatch, playlist_payload={"data": playlists})

    # The playlist choice is random, so repeat to make sure small ones never win
    for _ in range(20):
        music_service._recent_track_ids.clear()
        assert get_song_from_playlist("sad")["name"] == "Test Song"

    assert set(fake.fetched_playlists()) == {"2"}


def test_only_small_playlists_returns_no_song(monkeypatch):
    playlists = [make_playlist(1, 29), make_playlist(2, 10)]
    fake = use_playlist_fake(monkeypatch, playlist_payload={"data": playlists})

    assert get_song_from_playlist("sad") == NO_SONG
    assert fake.fetched_playlists() == []


@pytest.mark.parametrize("failing_step", ["playlist search", "playlist tracks"])
def test_playlist_deezer_error_returns_no_song(monkeypatch, failing_step):
    error = {"error": {"type": "Exception", "message": "Quota limit exceeded", "code": 4}}
    if failing_step == "playlist search":
        use_playlist_fake(monkeypatch, playlist_payload=error)
    else:
        use_playlist_fake(monkeypatch, playlist_payload={"data": [make_playlist(111, 50)]}, tracks_payload=error)

    assert get_song_from_playlist("angry") == NO_SONG


def test_playlist_network_failure_returns_no_song(monkeypatch):
    use_playlist_fake(monkeypatch, exc=urllib.error.URLError("connection refused"))

    assert get_song_from_playlist("relaxed") == NO_SONG
