import os
import cv2
import torch
import yt_dlp
import numpy as np
import timm
import logging
from torchvision import transforms
from PIL import Image
from facenet_pytorch import MTCNN

# 🔹 Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# 🔹 Set device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 🔹 Load Pre-trained Model
MODEL_PATH = r"C:\Users\vimal\Git_Projects\Deepfake\xception-43020ad28.pth"

try:
    # Load Xception model without classifier
    model = timm.create_model('xception', pretrained=False, num_classes=1000)

    # Modify classifier to match 2 output classes (Real vs Deepfake)
    model.fc = torch.nn.Linear(in_features=2048, out_features=2, bias=True)

    # Load trained weights
    state_dict = torch.load(MODEL_PATH, map_location=device)

    # Remove mismatched 'fc' layer weights to avoid loading errors
    state_dict = {k: v for k, v in state_dict.items() if not k.startswith('fc')}
    
    # Load weights with non-strict matching (to handle new classifier layer)
    model.load_state_dict(state_dict, strict=False)

    model.to(device)
    model.eval()
    
    logging.info("✅ Deepfake detection model loaded successfully.")
except Exception as e:
    logging.error(f"❌ Model loading failed: {e}")
    model = None

# 🔹 Image Transformations
transform = transforms.Compose([
    transforms.Resize((299, 299)),  # Xception requires 299x299 input
    transforms.ToTensor(),
    transforms.Normalize([0.5], [0.5])
])

# 🔹 Initialize Face Detector (MTCNN)
face_detector = MTCNN(keep_all=True, device=device)

# 🔹 Define Media Paths
MEDIA_PATH = r"C:\Users\vimal\Git_Projects\Deepfake\media\uploads"
FACE_PATH = os.path.join(MEDIA_PATH, "faces")  # Directory for saving extracted faces
os.makedirs(FACE_PATH, exist_ok=True)

# 🔹 Deepfake Prediction Function
def detect_deepfake(image_path):
    """Predicts whether an image is a deepfake using the AI model."""
    if not os.path.exists(image_path) or model is None:
        logging.error(f"❌ Image not found or model not loaded: {image_path}")
        return "Unknown"
    
    try:
        image = Image.open(image_path).convert("RGB")
        image = transform(image).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model(image)
            confidence = torch.nn.functional.softmax(output, dim=1)[0] * 100
            predicted = torch.argmax(output, dim=1).item()

        label = "Deepfake" if predicted == 1 else "Real"
        confidence_score = confidence[predicted].item()
        
        logging.info(f"🎯 Prediction: {label} ")
        return label  # Returning "Deepfake" or "Real"
    
    except Exception as e:
        logging.error(f"❌ Deepfake prediction error: {e}")
        return "Unknown"

# 🔹 Face Extraction from Video
def extract_faces(video_path, frame_skip=5):
    """Extracts faces from a video using MTCNN and saves them as images."""
    
    if not os.path.exists(video_path):
        logging.error(f"❌ Video file not found: {video_path}")
        return []

    logging.info(f"📂 Processing video: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logging.error(f"❌ Failed to open video: {video_path}")
        return []

    frame_count, saved_faces = 0, []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0:
            try:
                frame_pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                boxes, _ = face_detector.detect(frame_pil)

                if boxes is not None:
                    for i, box in enumerate(boxes):
                        x1, y1, x2, y2 = map(int, box)
                        face = frame[y1:y2, x1:x2]

                        if face.size == 0:
                            continue

                        face_filename = f"face_{frame_count}_{i}.jpg"
                        face_path = os.path.join(FACE_PATH, face_filename)
                        cv2.imwrite(face_path, face)
                        saved_faces.append(face_path)

            except Exception as e:
                logging.warning(f"⚠️ Face extraction error: {e}")

        frame_count += 1

    cap.release()
    
    logging.info(f"✅ Extracted {len(saved_faces)} faces from video.")
    return saved_faces

# 🔹 Classify Final Video Result
def classify_video_deepfake(faces):
    """
    Determines if the entire video is Deepfake or Real.
    If at least 25 faces are classified as 'Deepfake', classify the video as 'Deepfake'.
    Otherwise, classify it as 'Real'.
    """
    if not faces:
        logging.warning("⚠️ No faces detected, unable to classify.")
        return "Unknown"

    deepfake_count = sum(1 for face in faces if detect_deepfake(face) == "Deepfake")
    
    # ✅ Classify video based on threshold
    final_classification = "Deepfake" if deepfake_count >= 50 else "Real"

    logging.info(f"🎯 Final Video Classification: {final_classification} ")
    
    return final_classification
