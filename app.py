from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, yt_dlp
import uuid

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

# Serve frontend
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)

# Search YouTube
@app.route("/api/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])

    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "default_search": "auto",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            results = info.get("entries", [])

        songs = []
        for r in results:
            if r is None:
                continue
            songs.append({
                "id": r.get("id"),
                "title": r.get("title", "Unknown Title"),
                "thumbnail": r.get("thumbnail", f"https://img.youtube.com/vi/{r.get('id')}/mqdefault.jpg"),
                "composer": r.get("uploader") or "Unknown"
            })
        return jsonify(songs)
    except Exception as e:
        print("Search error:", e)
        return jsonify({"error": str(e)}), 500

# Play YouTube audio
@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "No video_id provided"}), 400

    try:
        # Generate temp filename
        temp_filename = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.m4a")

        ydl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": temp_filename,
            "quiet": True,
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "source_address": "0.0.0.0",  # Force IPv4
            "socket_timeout": 10
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
            if not info:
                return jsonify({"error": "Unable to fetch video"}), 500

        # Return relative path for frontend
        relative_path = f"/{TEMP_DIR}/{os.path.basename(temp_filename)}"
        return jsonify({"url": relative_path})
    except Exception as e:
        print("Play error:", e)
        return jsonify({"error": str(e)}), 500

# Run app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
