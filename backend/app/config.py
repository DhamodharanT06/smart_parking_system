import os
from pathlib import Path

# Base directory - project root (parent of backend folder)
BASE_DIR = Path(__file__).parent.parent.parent

# YOLO Model - resolve to project root
MODEL_PATH = os.path.join(BASE_DIR, os.getenv("MODEL_PATH", "yolov8n.pt"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.2))

# Slots configuration - resolve to project root
SLOTS_FILE = os.path.join(BASE_DIR, os.getenv("SLOTS_FILE", "slots.json"))

# Camera configuration
DEFAULT_CAMERA_INDEX = 0
DEFAULT_VIDEO_FILE = os.path.join(BASE_DIR, "parking_video.mp4")

# Video streaming
FPS = 30
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
JPEG_QUALITY = 80

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# CORS
CORS_ORIGINS = ["*"]
