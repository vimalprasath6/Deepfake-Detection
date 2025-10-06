import yt_dlp
import re
import os
import logging
from Application.deepfake_model import classify_video_deepfake  # Import your model function

# 🔹 Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 Ensure output directory exists
DOWNLOAD_PATH = os.path.join("media", "downloads")  # Save to 'media/downloads'
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

# 🔹 Validate URL
def is_valid_url(url):
    url_regex = re.compile(r'^(https?://)?(www\.)?([a-zA-Z0-9.-]+)\.(com|net|org)/')
    return re.match(url_regex, url) is not None

# 🔹 Download video from URL
def download_video(video_url):
    """Downloads video and returns file path."""
    if not is_valid_url(video_url):
        logging.error("❌ Invalid URL provided.")
        return None

    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'quiet': True,
        'noprogress': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            file_name = f"{info['title']}.mp4"
            file_path = os.path.join(DOWNLOAD_PATH, file_name)
        logging.info(f"✅ Video downloaded: {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"❌ Download error: {e}")
        return None

# 🔹 Analyze downloaded video
def analyze_video_from_url(video_url):
    """Downloads video and runs deepfake detection."""
    logging.info(f"📥 Downloading video from: {video_url}")
    
    video_path = download_video(video_url)  # Download the video
    
    if not video_path:
        return {"error": "Video download failed"}

    logging.info(f"🧠 Running deepfake detection on: {video_path}")
    
    deepfake_result = classify_video_deepfake(video_path)  # Run the model

    logging.info(f"🧠 Deepfake Detection Result: {deepfake_result}")

    return {"result": deepfake_result, "file_path": video_path}  # Return analysis result

# ✅ Example usage (For Testing)
if __name__ == "__main__":
    video_link = input("Enter video URL: ").strip()
    if video_link:
        result = analyze_video_from_url(video_link)
        print("🔍 Analysis Result:", result)
