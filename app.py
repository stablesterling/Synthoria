from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, yt_dlp

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# Serve frontend
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)

# API routes
@app.route("/api/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])

    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "skip_download": True,
        "default_search": "ytsearch10"
    }

    results = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            for entry in info.get("entries", []):
                results.append({
                    "id": entry.get("id"),
                    "title": entry.get("title", "No Title"),
                    "thumbnail": entry.get("thumbnail", ""),
                    "composer": entry.get("uploader", "Unknown")
                })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify(results)

@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "No video_id provided"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {"format": "bestaudio/best", "quiet": True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info.get("url")
            return jsonify({"url": audio_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
