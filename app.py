from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, yt_dlp

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# -------------------
# Serve frontend
# -------------------

@app.route("/")
def index():
    # Serve index.html at root
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    # Serve all static files (JS, CSS, images)
    return send_from_directory(".", path)

# -------------------
# Example API routes
# -------------------

# Sample search route
@app.route("/api/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])

    # Example: return dummy search results
    results = [
        {
            "id": "abc123",
            "title": f"Sample Song for {query}",
            "thumbnail": "https://via.placeholder.com/200x150.png?text=Song",
            "composer": "Unknown Artist"
        }
    ]
    return jsonify(results)

# Sample play route
@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "No video_id provided"}), 400

    # Example: return dummy audio URL
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    return jsonify({"url": audio_url})

# -------------------
# Run app
# -------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
