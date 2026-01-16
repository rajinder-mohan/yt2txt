# pip install yt-dlp

import yt_dlp
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def get_ytdlp_options(base_opts: dict = None) -> dict:
    """
    Get yt-dlp options with cookie support if configured.
    
    Supports:
    - YOUTUBE_COOKIES_FILE: Path to cookies file (Netscape format)
    - YOUTUBE_COOKIES_BROWSER: Browser to extract cookies from (e.g., 'chrome', 'firefox', 'edge')
    """
    if base_opts is None:
        base_opts = {}
    
    # Check for cookies configuration
    cookies_file = os.getenv("YOUTUBE_COOKIES_FILE")
    cookies_browser = os.getenv("YOUTUBE_COOKIES_BROWSER")
    
    # Add cookies if configured
    if cookies_file and os.path.exists(cookies_file):
        base_opts["cookies"] = cookies_file
    elif cookies_browser:
        # Support browser-based cookies (requires yt-dlp with browser support)
        base_opts["cookiesfrombrowser"] = (cookies_browser,)
    
    return base_opts


def download_audio(url, out_dir="audio"):
    os.makedirs(out_dir, exist_ok=True)

    base_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{out_dir}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
    }
    
    # Add cookie support if configured
    ydl_opts = get_ytdlp_options(base_opts)

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    download_audio("https://www.youtube.com/watch?v=VIDEO_ID")

