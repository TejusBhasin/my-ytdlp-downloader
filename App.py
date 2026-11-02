import os
import shutil
import zipfile
from flask import Flask, render_template_string, request, send_file
import yt_dlp

app = Flask(__name__)

# Stunning Glassmorphism Dark Theme UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Media Downloader</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background: linear-gradient(135deg, #0f0c20 0%, #15102a 100%);
            color: #e2e8f0;
            font-family: 'Segoe UI', system-ui, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 24px;
            padding: 40px;
            width: 100%;
            max-width: 550px;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4);
        }
        h1 {
            font-size: 2rem;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 30px;
            text-align: center;
            font-weight: 700;
        }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #94a3b8; font-size: 0.9rem; }
        input[type="text"] {
            width: 100%;
            padding: 14px 16px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: #fff;
            font-size: 1rem;
            transition: all 0.3s;
        }
        input[type="text"]:focus {
            outline: none;
            border-color: #6366f1;
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        .options-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 15px;
            margin-bottom: 25px;
        }
        .option-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.05);
            padding: 14px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .option-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.15);
        }
        .option-card input { margin-right: 12px; transform: scale(1.2); accent-color: #a855f7; }
        .btn {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            border: none;
            border-radius: 12px;
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.5);
        }
        .status { text-align: center; margin-top: 15px; color: #10b981; font-weight: 500; }
    </style>
</head>
<body>
    <div class="container">
        <h1>µDownloader</h1>
        <form method="POST">
            <div class="form-group">
                <label for="url">Playlist or Video URL</label>
                <input type="text" id="url" name="url" placeholder="https://youtube.com..." required>
            </div>
            
            <label>Customizations</label>
            <div class="options-grid">
                <label class="option-card">
                    <input type="radio" name="format" value="mp3" checked> Extract MP3 Audio
                </label>
                <label class="option-card">
                    <input type="radio" name="format" value="mp4"> Download MP4 Video
                </label>
                <label class="option-card">
                    <input type="checkbox" name="thumbnail" value="yes"> Include Album Art
                </label>
                <label class="option-card">
                    <input type="checkbox" name="metadata" value="yes"> Embed Metadata
                </label>
            </div>
            
            <button type="submit" class="btn">Process & Package into ZIP</button>
        </form>
        {% if status %}
            <div class="status">{{ status }}</div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        url = request.form.get('url')
        fmt = request.form.get('format')
        embed_thumb = request.form.get('thumbnail')
        embed_meta = request.form.get('metadata')
        
        # Clean build directories
        dl_dir = os.path.join(os.getcwd(), 'downloads_pack')
        if os.path.exists(dl_dir): shutil.rmtree(dl_dir)
        os.makedirs(dl_dir)
        
        # Construct yt-dlp rules dynamically based on checkbox customizations
        ydl_opts = {
            'outtmpl': f'{dl_dir}/%(title)s.%(ext)s',
            'ignoreerrors': True,
        }
        
        if fmt == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocs': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
            if embed_thumb:
                ydl_opts['postprocs'].append({'key': 'FFmpegThumbnailsConvertor', 'format': 'jpg'})
                ydl_opts['writethumbnail'] = True
                ydl_opts['postprocs'].append({'key': 'EmbedThumbnail', 'already_have_thumbnail': False})
            if embed_meta:
                ydl_opts['postprocs'].append({'key': 'FFmpegMetadata', 'add_metadata': True})
        else:
            ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
            if embed_meta:
                ydl_opts['postprocs'] = [{'key': 'FFmpegMetadata', 'add_metadata': True}]

        # Execute yt-dlp download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Compress all downloaded items into a clean file zip bundle
        zip_path = os.path.join(os.getcwd(), 'playlist_package.zip')
        if os.path.exists(zip_path): os.remove(zip_path)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dl_dir):
                for file in files:
                    if not file.endswith('.jpg') and not file.endswith('.webp'): # Skip loose artwork crumbs
                        zipf.write(os.path.join(root, file), file)
                        
        return send_file(zip_path, as_attachment=True, download_name='media_package.zip')

    return render_template_string(HTML_TEMPLATE, status=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
