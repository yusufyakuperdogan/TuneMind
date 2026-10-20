import os
import sys

import pytest

# The backend imports modules as "services.*", so make backend/ importable
# no matter which directory pytest is started from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import services.emotion_service as emotion_service  # noqa: E402
from services.emotion_service import detect_emotion  # noqa: E402


@pytest.mark.parametrize(
    "text, expected",
    [
        ("I just got promoted, I can't stop smiling!", "happy"),
        ("I miss my old friends and feel so alone.", "sad"),
        ("I am furious, they lied to me again!", "angry"),
        ("It's a quiet, cozy evening at home.", "relaxed"),
        ("The bus was on time this morning.", "neutral"),
    ],
)
def test_detect_emotion(text, expected):
    assert detect_emotion(text) == expected


def test_empty_string_returns_neutral():
    assert detect_emotion("") == "neutral"


def test_whitespace_returns_neutral_without_calling_model(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("model should not be called for whitespace-only text")

    monkeypatch.setattr(emotion_service, "emotion_classifier", fail_if_called)
    assert detect_emotion(" ") == "neutral"
