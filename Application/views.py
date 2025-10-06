
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
import os
import cv2
import logging
from PIL import Image
from facenet_pytorch import MTCNN
from .deepfake_model import extract_faces  # ✅ Importing correctly
from Application.deepfake_model import extract_faces, classify_video_deepfake  # ✅ Import final classification function
from Application.video_downloader import analyze_video_from_url  # Import function


# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize face detector
face_detector = MTCNN(keep_all=True)

import yt_dlp  # Download social media videos
from pytube import YouTube  # Download YouTube videos
from Application.deepfake_model import detect_deepfake  # Only import image detection

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Ensure MEDIA_PATH exists
MEDIA_PATH = os.path.join(settings.MEDIA_ROOT, "uploads")
os.makedirs(MEDIA_PATH, exist_ok=True)


def index1_view(request):
    """Render the homepage."""
    return render(request, "homepage.html")


@csrf_exempt
def upload_file(request):
    """Handles file uploads."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    if "video" not in request.FILES:
        logging.error("❌ No video file found in request.")
        return JsonResponse({"error": "No video file uploaded"}, status=400)

    video_file = request.FILES["video"]
    file_extension = os.path.splitext(video_file.name)[1].lower()

    # ✅ Allowed video formats
    allowed_extensions = [".mp4", ".avi", ".mov", ".mkv"]
    if file_extension not in allowed_extensions:
        logging.error(f"❌ Unsupported file format: {file_extension}")
        return JsonResponse({"error": "Invalid file format"}, status=400)

    # ✅ Sanitize filename to prevent security issues
    safe_filename = "".join(c if c.isalnum() or c in (".", "_", "-") else "_" for c in video_file.name)
    video_path = os.path.join(MEDIA_PATH, safe_filename)

    try:
        # ✅ Save uploaded video
        with open(video_path, "wb+") as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)

        logging.info(f"✅ File uploaded: {video_path}")

        return JsonResponse({"file_url": video_path}, status=200)

    except Exception as e:
        logging.error(f"❌ Error saving video: {e}")
        return JsonResponse({"error": "Internal server error"}, status=500)



@csrf_exempt
def download_video(request):
    """Download a video from a social media link and store it in media/uploads/."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            video_url = data.get("video_url")

            if not video_url:
                return JsonResponse({"error": "No URL provided"}, status=400)

            file_path, file_name = fetch_video(video_url)

            if file_path:
                logging.info(f"✅ Video downloaded successfully: {file_path}")
                return JsonResponse({"file_url": f"/media/uploads/{file_name}"})
            else:
                return JsonResponse({"error": "Failed to download video"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def fetch_video(url):
    """Download video from YouTube or other social media and save it to media/uploads."""
    try:
        # Check if the URL is from YouTube
        if "youtube.com" in url or "youtu.be" in url:
            yt = YouTube(url)
            video = yt.streams.filter(progressive=True, file_extension="mp4").first()
            file_name = f"{yt.title}.mp4".replace(" ", "_")
            file_path = os.path.join(MEDIA_PATH, file_name)
            video.download(output_path=MEDIA_PATH, filename=file_name)
        else:
            # Use yt_dlp for other social media platforms (Instagram, TikTok, etc.)
            ydl_opts = {
                "outtmpl": os.path.join(MEDIA_PATH, "%(title)s.%(ext)s"),
                "format": "bestvideo+bestaudio/best",
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = os.path.join(MEDIA_PATH, f"{info['title']}.mp4")
                file_name = f"{info['title']}.mp4"

        logging.info(f"✅ Video fetched: {file_path}")
        return file_path, file_name

    except Exception as e:
        logging.error(f"Video download error: {e}")
        return None, None


@csrf_exempt
def analyze_media(request):
    """Analyze an uploaded image or video for deepfake detection."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            file_name = data.get("file_name")

            if not file_name:
                return JsonResponse({"error": "No file specified"}, status=400)

            file_path = os.path.join(MEDIA_PATH, file_name)

            if not os.path.exists(file_path):
                return JsonResponse({"error": "File not found"}, status=404)

            if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                result = detect_deepfake(file_path)
                logging.info(f"🛠 Deepfake Analysis Result: {result}")
            elif file_name.lower().endswith((".mp4", ".mov", ".webm")):
                result = analyze_media(file_path)  # Now inside views.py
                logging.info(f"🛠 Video Analysis Result: {result}")
            else:
                return JsonResponse({"error": "Unsupported file format"}, status=400)

            return JsonResponse({"result": result})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)




@csrf_exempt
def analyze_file(request):
    """Handles deepfake analysis after file upload."""
    
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)

    try:
        # ✅ Parse JSON data from frontend
        data = json.loads(request.body)
        video_path = data.get("file_url")  # Get the uploaded video path

        # ✅ Check if file exists
        if not video_path or not os.path.exists(video_path):
            logging.error(f"❌ Video file not found: {video_path}")
            return JsonResponse({"error": "Video file not found"}, status=400)

        logging.info(f"📂 Processing video: {video_path}")

        # ✅ Extract faces from video
        faces = extract_faces(video_path)  

        if not faces:
            logging.warning("⚠️ No faces detected in video.")
            return JsonResponse({"error": "No faces detected"}, status=400)

        # ✅ Run deepfake classification on extracted faces
        final_result = classify_video_deepfake(faces)

        # ✅ Log and return the final classification
        logging.info(f"🎯 Final Classification: {final_result}")

        return JsonResponse({"status": "success", "result": final_result}, status=200)

    except json.JSONDecodeError:
        logging.error("❌ Invalid JSON format in request.")
        return JsonResponse({"error": "Invalid JSON data"}, status=400)

    except Exception as e:
        logging.error(f"🔥 Internal Server Error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
def analyze_url(request):
    """Handles deepfake detection for videos from a URL."""
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        video_url = data.get("video_url")

        if not video_url:
            return JsonResponse({"error": "No URL provided"}, status=400)

        logging.info(f"📩 Processing URL: {video_url}")

        result = analyze_video_from_url(video_url)  # Call video analysis function

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON format"}, status=400)
