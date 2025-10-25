from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid, shutil, atexit, yt_dlp

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

TEMP_DIR = "temp_song"
SAVED_DIR = "saved_songs"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)

def clear_temp():
    for f in os.listdir(TEMP_DIR):
        os.remove(os.path.join(TEMP_DIR, f))
atexit.register(clear_temp)


# ✅ Serve frontend files (HTML/JS/CSS)
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/<path:path>")
def serve_static(path):
    return send_from_directory(".", path)


# ✅ Search API
@app.route("/api/search")
def search():
    query = request.args.get("q")
    if not query:
        return jsonify([])
    try:
        ydl_opts = {"quiet": True, "extract_flat": True, "skip_download": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(f"ytsearch10:{query}", download=False)["entries"]

        songs = []
        for r in results:
            songs.append({
                "id": r["id"],
                "title": r.get("title", "Unknown Title"),
                "thumbnail": r.get("thumbnail", f"https://img.youtube.com/vi/{r['id']}/mqdefault.jpg")
            })
        return jsonify(songs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Play/Convert YouTube audio
@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    try:
        for f in os.listdir(TEMP_DIR):
            os.remove(os.path.join(TEMP_DIR, f))

        temp_filename = f"{uuid.uuid4()}.mp3"
        output_path = os.path.join(TEMP_DIR, temp_filename)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }],
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)

        return jsonify({
            "title": info.get("title", "Track"),
            "filename": temp_filename,
            "url": f"/temp/{temp_filename}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/temp/<filename>")
def serve_temp(filename):
    return send_from_directory(TEMP_DIR, filename)


# ✅ Saving songs
@app.route("/api/save", methods=["POST"])
def save_song():
    data = request.get_json()
    filename = data.get("filename")
    title = data.get("title", "song")

    if not filename:
        return jsonify({"error": "Missing filename"}), 400

    safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "_", "-")]).rstrip()
    src = os.path.join(TEMP_DIR, filename)
    dst = os.path.join(SAVED_DIR, f"{safe_title}.mp3")

    if os.path.exists(src):
        shutil.copy(src, dst)
        return jsonify({"message": f"Saved as {safe_title}.mp3"})

    return jsonify({"error": "Temp file not found"}), 404


@app.route("/api/saved")
def saved_songs():
    files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".mp3")]
    return jsonify(files)


@app.route("/saved/<filename>")
def serve_saved(filename):
    return send_from_directory(SAVED_DIR, filename)


# ✅ Render deployment fix — use PORT environment variable
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
