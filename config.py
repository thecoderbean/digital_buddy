"""Central configuration for the Sci-Fi AI Digital Companion."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class Config:
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"

    # Camera
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", 0))
    FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", 960))
    FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", 540))
    JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", 85))
    TARGET_FPS = int(os.getenv("TARGET_FPS", 30))

    # Models
    FACE_MODEL_PATH = os.path.join(BASE_DIR, "models", "face_landmarker.task")
    HAND_MODEL_PATH = os.path.join(BASE_DIR, "models", "hand_landmarker.task")
    FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

    # Emotion smoothing (EMA)
    EMOTION_ALPHA = 0.35          # 0..1, higher = more reactive
    EMOTION_MIN_CONFIDENCE = 0.45
    EMOTION_STABILITY_FRAMES = 3

    # Threading
    CAPTURE_QUEUE_SIZE = 2