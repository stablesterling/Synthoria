from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/api/search')
def search():
    query = request.args.get('q')
    if not query:
        return jsonify([])

    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'skip_download': True,
        'default_search': 'ytsearch10',  # get top 10 results
    }

    results = []
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(query, download=False)
        for entry in info['entries']:
            results.append({
                'id': entry['id'],
                'title': entry.get('title', 'No Title'),
                'thumbnail': entry.get('thumbnail', ''),
                'composer': entry.get('uploader', 'Unknown')
            })
    return jsonify(results)

@app.route('/api/play', methods=['POST'])
def play():
    data = request.get_json()
    video_id = data.get('video_id')
    if not video_id:
        return jsonify({'error': 'No video_id provided'}), 400

    url = f'https://www.youtube.com/watch?v={video_id}'
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info['url']
            return jsonify({'url': audio_url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
