# 🎵 TuneMind - Emotion Music

[![tests](https://github.com/yusufyakuperdogan/TuneMind/actions/workflows/tests.yml/badge.svg)](https://github.com/yusufyakuperdogan/TuneMind/actions/workflows/tests.yml)

TuneMind detects your emotion from text and plays a matching song from Deezer.

## Screenshots

### Main Screen
![Main Screen](screenshots/main_screen.png)

### Happy
![Happy](screenshots/happy.png)

### Sad
![Sad](screenshots/sad.png)

### Angry
![Angry](screenshots/angry.png)

### Neutral
![Neutral](screenshots/neutral.png)

## Technologies
- Backend: FastAPI, Python
- Emotion Detection: Hugging Face (j-hartmann/emotion-english-distilroberta-base)
- Music: Deezer public API (no API key or account needed)
- Frontend: HTML, CSS, JavaScript

## Setup

### 1. Clone the repository
```
git clone https://github.com/60yusuf60/TuneMind.git
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run the backend
```
cd backend
uvicorn main:app --reload
```

### 4. Open frontend
Open `frontend/index.html` in your browser.

## How It Works
1. User types how they feel
2. Hugging Face AI model detects the emotion
3. The Deezer public API is searched with emotion-based queries to find a matching song
4. Song plays directly in the browser via the Deezer embed player (30-second preview without a Deezer login)

## Supported Emotions

| Emotion | Example sentence |
|---|---|
| 😊 Happy | "I just got promoted, I can't stop smiling!" |
| 😢 Sad | "I miss my old friends and feel so alone." |
| 😠 Angry | "I am furious, they lied to me again!" |
| 😌 Relaxed | "It's a quiet, cozy evening at home." |
| 😐 Neutral | "The bus was on time this morning." |

**Relaxed** is detected from calm keywords: if the text contains *calm*, *peaceful*, *relaxed*, *chill*, *quiet*, *cozy*, *sleepy* or *at ease*, and the model reads it as neutral, joy or surprise, TuneMind treats it as relaxed.