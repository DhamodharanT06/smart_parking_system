import cv2
import numpy as np
import os
import time
from typing import Generator, Optional, Tuple, Dict
from pathlib import Path


# Create debug frames directory (absolute path)
BACKEND_DIR = Path(__file__).parent.parent.parent  # Points to backend/ folder
DEBUG_FRAMES_DIR = str(BACKEND_DIR / "debug_frames")

if not os.path.exists(DEBUG_FRAMES_DIR):
    os.makedirs(DEBUG_FRAMES_DIR)

print(f"Debug frames directory: {DEBUG_FRAMES_DIR}")


class VideoStreamHandler:
    """Handle video streaming in MJPEG format with brightness normalization"""
    
    def __init__(self, fps: int = 30, width: int = 1280, height: int = 720, quality: int = 80):
        self.fps = fps
        self.width = width
        self.height = height
        self.quality = quality
        self.frame_skip = 0
    
    @staticmethod
    def normalize_brightness(frame: np.ndarray) -> np.ndarray:
        """Apply brightness normalization per paper: (frame - mean) / std_dev"""
        if frame is None:
            return frame
        try:
            # Convert to float for normalization
            frame_float = frame.astype(np.float32)
            mean = np.mean(frame_float)
            std = np.std(frame_float)
            
            # Avoid division by zero
            if std < 1e-6:
                return frame
            
            # Normalize
            normalized = (frame_float - mean) / std
            
            # Scale back to 0-255 range
            normalized = np.clip((normalized + 1) * 127.5, 0, 255).astype(np.uint8)
            return normalized
        except Exception as e:
            print(f"Warning: Brightness normalization failed: {e}")
            return frame
    
    def encode_frame_to_jpeg(self, frame: np.ndarray) -> bytes:
        """Encode OpenCV frame to JPEG bytes"""
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
        if ret:
            return buffer.tobytes()
        return None
    
    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resize frame to configured dimensions"""
        return cv2.resize(frame, (self.width, self.height))
    
    def generate_mjpeg_stream(self, frame_generator: Generator) -> Generator:
        """
        Generate MJPEG stream from frame generator, capped at ~25 fps.

        Yields:
            MJPEG boundary and frame data
        """
        frame_interval = 1.0 / 25  # target 25 fps
        try:
            for frame in frame_generator:
                if frame is None:
                    continue

                t0 = time.time()

                # Resize
                frame = self.resize_frame(frame)

                # Encode
                jpeg = self.encode_frame_to_jpeg(frame)
                if jpeg:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(jpeg)).encode() + b'\r\n'
                           b'\r\n' + jpeg + b'\r\n')

                # Throttle to target fps
                elapsed = time.time() - t0
                sleep_for = frame_interval - elapsed
                if sleep_for > 0:
                    time.sleep(sleep_for)
        except GeneratorExit:
            pass
    
    @staticmethod
    def get_video_info(cap: cv2.VideoCapture) -> Dict:
        """Get video information"""
        return {
            "fps": int(cap.get(cv2.CAP_PROP_FPS)),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        }
    
    @staticmethod
    def save_debug_frame(frame: np.ndarray, camera_id: str) -> str:
        """Save individual frame as JPEG image file"""
        try:
            filename = "debug_frame_root.jpg"
            filepath = os.path.join(DEBUG_FRAMES_DIR, filename)
            cv2.imwrite(filepath, frame)
            print(f"✓ Saved frame: {filepath}")
            return filepath
        except Exception as e:
            print(f"❌ Error saving debug frame: {e}")
            return None
    
    @staticmethod
    def get_debug_frame_path(camera_id: str) -> Optional[str]:
        """Get path to debug frame if it exists"""
        filepath = os.path.join(DEBUG_FRAMES_DIR, "debug_frame_root.jpg")
        if os.path.exists(filepath):
            return filepath
        return None
