import os
import sys

import pytest

# The backend imports modules as "services.*", so make backend/ importable
# no matter which directory pytest is started from.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.emotion_service import detect_emotion  # noqa: E402

VALID_EMOTIONS = {"happy", "sad", "angry", "relaxed", "neutral"}


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


def test_empty_string_returns_valid_emotion():
    assert detect_emotion("") in VALID_EMOTIONS
