from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, uuid, shutil, atexit, yt_dlp, time

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

TEMP_DIR = "temp_song"
SAVED_DIR = "saved_songs" # This acts as the server-side "VoFo" folder for permanent storage
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(SAVED_DIR, exist_ok=True)


# Automatically clean temporary files older than 10 minutes
def clear_old_temp():
    """Removes files in TEMP_DIR older than 10 minutes (600 seconds)."""
    now = time.time()
    for f in os.listdir(TEMP_DIR):
        path = os.path.join(TEMP_DIR, f)
        # Check if the path is a file and is older than 600 seconds
        if os.path.isfile(path) and now - os.path.getmtime(path) > 600:
            try:
                os.remove(path)
            except Exception:
                pass

# Register the cleanup function to run on exit
atexit.register(clear_old_temp)


# Serve frontend
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path != "" and os.path.exists(path):
        return send_from_directory(".", path)
    return send_from_directory(".", "tedt.html")


# YouTube Search API
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
            "ignoreerrors": True,
            "default_search": "auto"
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Modified from ytsearch10 to ytsearch50 to return up to 50 results
            info = ydl.extract_info(f"ytsearch50:{query}", download=False)
            results = info.get("entries", [])

        songs = []
        for r in results:
            if not r or not r.get("id"):
                continue
            songs.append({
                "id": r.get("id"),
                "title": r.get("title", "Unknown Title"),
                "thumbnail": r.get("thumbnail", f"https://img.youtube.com/vi/{r.get('id')}/mqdefault.jpg"),
                "composer": r.get("uploader", "Unknown")
            })
        return jsonify(songs)

    except Exception as e:
        print("Search error:", e)
        return jsonify({"error": str(e)}), 500


# Download YouTube audio and convert to MP3 (Optimized for error handling)
@app.route("/api/play", methods=["POST"])
def play():
    data = request.get_json()
    video_id = data.get("video_id")
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    # Use a unique ID to track the file regardless of race conditions
    temp_id = str(uuid.uuid4())
    
    try:
        clear_old_temp()
        
        ydl_opts = {
            # 'bestaudio/best' ensures highest quality audio is found, falling back to combined streams if needed
            "format": "bestaudio/best",
            # Ensure the output filename is predictable for later retrieval
            "outtmpl": os.path.join(TEMP_DIR, f"{temp_id}.%(ext)s"),
            # 'quiet': False exposes internal yt-dlp and FFmpeg errors to the console
            "quiet": False, 
            "noplaylist": True,
            # Removed 'ignoreerrors' so exceptions are properly caught
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }],
            "extractor_args": {
                "youtube": {
                    "player_skip": ["web_safari"],
                    "force_desktop": True
                }
            }
        }

        # Step 1: Download and Convert (Exception will be raised on failure)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)

        # Step 2: Verification
        final_filename = f"{temp_id}.mp3"
        final_filepath = os.path.join(TEMP_DIR, final_filename)

        if not os.path.exists(final_filepath):
            # If download succeeded but FFmpeg conversion failed (a silent failure), we raise an error
            raise IOError("FFmpeg conversion failed: Final MP3 file was not created.")

        # Step 3: Success Response
        return jsonify({
            "title": info.get("title", "Track"),
            "filename": final_filename, # This is the unique file ID needed for the download call
            "url": f"/temp/{final_filename}",
            "video_id": video_id # Include original video ID for related search
        })

    except yt_dlp.utils.DownloadError as e:
        # Handler for unplayable videos (age-restriction, geo-blocking, etc.)
        error_msg = f"Download failed (YouTube Restriction/Error): {e.exc_info[1] if e.exc_info else str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    except IOError as e:
        # Handler for failed FFmpeg conversion
        print(f"Conversion Error: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        # Catch-all for unexpected issues
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500
    finally:
        # Crucial: Clean up any partial/intermediate files with the unique ID
        for f in os.listdir(TEMP_DIR):
            if f.startswith(temp_id) and not f.endswith(".mp3"):
                try:
                    os.remove(os.path.join(TEMP_DIR, f))
                except Exception:
                    pass


# NEW Route: Get related video IDs for autoplay
@app.route("/api/related")
def get_related():
    video_id = request.args.get("video_id")
    if not video_id:
        return jsonify({"error": "Missing video_id"}), 400

    url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        ydl_opts = {
            "quiet": True,
            "extract_flat": "in_playlist", # Extracts related videos info
            "skip_download": True,
            "ignoreerrors": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info, specifically the 'related_videos' key
            info = ydl.extract_info(url, download=False)
            
        related = info.get("related_videos", [])
        
        # Filter and structure the related videos list
        related_songs = []
        for r in related:
            if not r or not r.get("id"):
                continue
            related_songs.append({
                "id": r.get("id"),
                "title": r.get("title", "Unknown Title"),
                "composer": r.get("channel", r.get("uploader", "Unknown")),
            })
            # We only need the top 5 related songs
            if len(related_songs) >= 5:
                break

        return jsonify(related_songs)

    except Exception as e:
        print("Related search error:", e)
        return jsonify({"error": str(e)}), 500


# Serve temporary files
@app.route("/temp/<filename>")
def serve_temp(filename):
    path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_from_directory(TEMP_DIR, filename)


# Download and permanently save the song (and trigger client download)
@app.route("/api/download", methods=["POST"])
def download_song():
    data = request.get_json()
    filename = data.get("filename") # The temporary filename (e.g., UUID.mp3)
    title = data.get("title", "song") # The song title for the saved file name

    if not filename:
        return jsonify({"error": "Missing temporary filename ('filename')"}), 400

    # 1. Check if temporary source file exists
    src = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(src):
        return jsonify({"error": "Temporary file not found. Please ensure the song was played recently."}), 404

    # 2. Sanitize title and determine the destination path in SAVED_DIR
    safe_title = "".join([c for c in title if c.isalnum() or c in (" ", "_", "-")]).rstrip()
    
    base_dst_name = f"{safe_title}.mp3"
    dst = os.path.join(SAVED_DIR, base_dst_name)
    
    # Handle duplicate saved filenames by appending a counter
    counter = 1
    final_saved_name = base_dst_name
    while os.path.exists(dst):
        final_saved_name = f"{safe_title} ({counter}).mp3"
        dst = os.path.join(SAVED_DIR, final_saved_name)
        counter += 1

    # 3. Copy the file from temporary location to permanent saved location (Server-side save)
    try:
        shutil.copy(src, dst)
    except Exception as e:
        print("Download/Save copy error:", e)
        return jsonify({"error": f"Failed to save file permanently: {str(e)}"}), 500

    # 4. Serve the file from the permanent saved location with attachment header (Client-side download)
    # The browser will use the 'final_saved_name' for the local download name.
    return send_from_directory(
        SAVED_DIR, 
        final_saved_name, 
        as_attachment=True, 
        mimetype='audio/mpeg'
    )


# List saved songs
@app.route("/api/saved")
def saved_songs():
    files = [f for f in os.listdir(SAVED_DIR) if f.endswith(".mp3")]
    return jsonify(files)


# Serve saved files (for listing/playing saved songs on the server)
@app.route("/saved/<filename>")
def serve_saved(filename):
    path = os.path.join(SAVED_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_from_directory(SAVED_DIR, filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
