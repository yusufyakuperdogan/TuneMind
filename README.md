# 🎵 TuneMind - Emotion Music

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
pip install fastapi uvicorn sqlalchemy transformers torch
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