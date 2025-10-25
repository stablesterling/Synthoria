from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route("/api/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])
    try:
        ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{query}", download=False)["entries"]
        songs = [{"id": r["id"], "title": r["title"], "thumbnail": r.get("thumbnail", f"https://img.youtube.com/vi/{r['id']}/mqdefault.jpg")} for r in results]
        return jsonify(songs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400
    try:
        ydl_opts = {"format": "bestaudio/best", "quiet": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
            audio_url = info["url"]
        return jsonify({"title": info["title"], "url": audio_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
