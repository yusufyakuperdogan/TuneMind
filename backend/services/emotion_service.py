import re

from transformers import pipeline

"""
Uses a pre-trained Hugging Face model to detect emotions from text.
Detected emotions are mapped to music search categories to fetch the perfect song.
"""

emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1
)

EMOTION_MAP = {
    "joy": "happy",
    "sadness": "sad",
    "anger": "angry",
    "fear": "sad",
    "disgust": "angry",
    "surprise": "happy",
    "neutral": "neutral"
}

# A "neutral" result becomes "relaxed" when the text contains one of these
# (whole words/phrases, case-insensitive).
CALM_WORDS = ["calm", "peaceful", "relaxed", "chill", "quiet", "cozy", "sleepy", "at ease"]
CALM_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w).replace(r"\ ", r"\s+") for w in CALM_WORDS) + r")\b",
    re.IGNORECASE
)

def detect_emotion(message: str) -> str:
    try:
        result = emotion_classifier(message)
        label = result[0][0]["label"].lower()
        emotion = EMOTION_MAP.get(label, "neutral")
        if emotion == "neutral" and CALM_PATTERN.search(message):
            return "relaxed"
        return emotion
    except Exception as e:
        print("Emotion detection error:", e)
        return "neutral"