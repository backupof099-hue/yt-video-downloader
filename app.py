import os
import io
from flask import Flask, request, render_template, flash, redirect, url_for, send_file
import yt_dlp

# --- Flask App Setup ---
app = Flask(__name__)
# Secret key ab Render ke environment variable se aayega
app.secret_key = os.environ.get('SECRET_KEY', 'local-secret-key-for-testing')

# --- Core Downloader Function (Updated for Memory Streaming) ---
def download_video_to_memory(url):
    """
    Video ko download karke memory (bytes) me rakhta hai.
    Video data aur file ka naam return karta hai.
    """
    try:
        buffer = io.BytesIO()
        
        # Pehle info nikalenge taaki filename mil sake
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl_info:
            info = ydl_info.extract_info(url, download=False)
            # File ka naam saaf-suthra rakho
            filename = f"{info.get('title', 'video')}.mp4"

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            # stdout par stream karne ke liye 'outtmpl': '-' use karte hain
            # lekin yt-dlp ko file-like object direct de sakte hain
            'outtmpl': '-',  # Hum isko stdout par bhejenge
            'logtostderr': True,
            'noplaylist': True,
        }

        # Ab video download karke buffer me daalenge
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ydl.download() output ko stdout me bhejta hai
            # jisko hum buffer me save kar rahe hain
            ydl.stdout = buffer
            ydl.download([url])
        
        buffer.seek(0)
        return buffer, filename

    except Exception as e:
        print(f"Download me error: {e}")
        return None, None

# --- Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def handle_download():
    url = request.form.get('url')
    if not url:
        flash("Bhai, URL to daalo!")
        return redirect(url_for('index'))
    
    print(f"URL mila: {url}. Download shuru kar rahe hain...")
    
    video_buffer, filename = download_video_to_memory(url)
    
    if video_buffer and filename:
        print(f"File '{filename}' memory me taiyaar hai. User ko bhej rahe hain...")
        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='video/mp4'
        )
    else:
        flash("Video download nahi ho paaya. Shayad URL galat hai, video private hai, ya fir bahut bada hai (server time-out ho gaya).")
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
