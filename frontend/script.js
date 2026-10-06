const analyzeBtn = document.getElementById("analyzeBtn");
const textInput = document.getElementById("textInput");
const resultDiv = document.getElementById("result");

// The text from the last analysis, re-sent by the "Another song" button
let lastText = "";

analyzeBtn.addEventListener("click", () => {
    const text = textInput.value.trim();
    if (!text) return alert("Please enter how you feel!");
    fetchSong(text);
});

async function fetchSong(text) {
    lastText = text;
    resultDiv.innerHTML = `<p class="loading">Analyzing your mood... 🎵</p>`;
    analyzeBtn.disabled = true;

    try {
        const response = await fetch("http://127.0.0.1:8000/emotion/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text })
        });

        const data = await response.json();

        if (data.song && data.song.track_id) {
            const emotion = escapeHtml(data.emotion.toLowerCase());
            resultDiv.innerHTML = `
                <span class="emotion-badge ${emotion}">
                    ${getEmotionEmoji(data.emotion)} ${emotion}
                </span>
                <div class="player-wrapper">
                    <iframe
                        title="Deezer player"
                        src="https://widget.deezer.com/widget/auto/track/${encodeURIComponent(data.song.track_id)}"
                        width="100%"
                        height="152"
                        frameBorder="0"
                        allowtransparency="true"
                        allow="encrypted-media; clipboard-write"
                        loading="lazy">
                    </iframe>
                </div>
                <div class="song-info">
                    <p class="song-name">${escapeHtml(data.song.name)}</p>
                    <p class="song-artist">${escapeHtml(data.song.artist)}</p>
                </div>
                <button id="anotherBtn" class="another-btn">🔄 Another song</button>
            `;
            document.getElementById("anotherBtn").addEventListener("click", () => fetchSong(lastText));
        } else {
            resultDiv.innerHTML = `<p class="error">No song found for this emotion. Try again!</p>`;
        }
    } catch (err) {
        resultDiv.innerHTML = `<p class="error">Error connecting to backend. Make sure the server is running!</p>`;
        console.error(err);
    } finally {
        analyzeBtn.disabled = false;
    }
}

// Make text from the API safe to put inside HTML
function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function getEmotionEmoji(emotion) {
    const emojis = {
        happy: "😊",
        sad: "😢",
        angry: "😠",
        relaxed: "😌",
        neutral: "😐"
    };
    return emojis[emotion.toLowerCase()] || "🎵";
}
