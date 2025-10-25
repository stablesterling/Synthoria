from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Root route so Render won't 404
@app.route("/")
def home():
    return "Synthoria backend is live!"

# Search route
@app.route("/api/search")
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
        }
        results = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_result = ydl.extract_info(f"ytsearch5:{query}", download=False)['entries']
            for entry in search_result:
                results.append({
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "thumbnail": entry.get("thumbnail"),
                    "composer": entry.get("uploader")
                })
        return jsonify(results)
    except Exception as e:
        print("Search error:", e)
        return jsonify({"error": "Failed to search"}), 500

# Play route
@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "video_id missing"}), 400

    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
        return jsonify({"url": audio_url})
    except Exception as e:
        print("Play error:", e)
        return jsonify({"error": "Failed to get audio"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
