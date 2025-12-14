import os
import io
from flask import Flask, request, render_template, flash, redirect, url_for, send_file
import yt_dlp

# --- Flask App Setup ---
app = Flask(__name__)
# Secret key ab Render ke environment variable se aayega
app.secret_key = os.environ.get('SECRET_KEY', 'ek-default-secret-key-jo-local-chalane-ke-liye-hai')


# --- Core Downloader Function (Updated for Memory Streaming) ---
def download_video_to_memory(url):
    """
    Video ko download karke memory (bytes) me rakhta hai.
    Video data aur file ka naam return karta hai.
    """
    try:
        buffer = io.BytesIO()
        ydl_opts = {
            # Best video (mp4) + best audio (m4a) ko merge karke final mp4 banao
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            # File disk par nahi, seedha buffer (memory) me jayegi
            'outtmpl': '-', 
            'logtostderr': True, # Errors ko console me dikhao
            'noplaylist': True,
            # FFmpeg ko batao ki output pipe (stdout) me bhejna hai
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            # Output ko stdout pe stream karo
            'outtmpl': {'default': '-'},
            'quiet': True,
        }

        # Pehle info nikalenge taaki filename mil sake
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl_info:
            info = ydl_info.extract_info(url, download=False)
            filename = f"{info['title']}.mp4"

        # Ab video download karke buffer me daalenge
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ydl.download() output ko stdout me bhejta hai
            # Jisko hum buffer me save kar rahe hain
            ydl.stdout = buffer
            ydl.download([url])
        
        # Buffer ko shuru me le aao
        buffer.seek(0)
        
        # Buffer (video data) aur filename return karo
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
    
    # Ye flash message shayad na dikhe kyunki agle step me file download shuru ho jaati hai
    # flash("Downloading shuru ho rahi hai... Please wait...")
    print(f"URL mila: {url}. Download shuru kar rahe hain...")
    
    video_buffer, filename = download_video_to_memory(url)
    
    if video_buffer and filename:
        print(f"File '{filename}' memory me taiyaar hai. User ko bhej rahe hain...")
        # User ko file memory se seedha serve karo
        return send_file(
            video_buffer,
            as_attachment=True,
            download_name=filename, # Ye file ka naam hoga jo user ke paas save hogi
            mimetype='video/mp4'
        )
    else:
        flash("Video download nahi ho paaya. Shayad URL galat hai, video private hai, ya fir bahut bada hai.")
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Ye block sirf local machine par test karne ke liye hai
    # Render isko use nahi karega, wo gunicorn use karega
    app.run(host='0.0.0.0', port=5000, debug=True)
