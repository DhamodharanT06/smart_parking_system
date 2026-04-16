import cv2
import json
import os
import threading
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import urllib.parse


class CameraManager:
    """Manage camera sources and configurations"""
    
    def __init__(self, slots_config_path: str = "slots.json", cameras_config_path: str = "cameras.json"):
        """Initialize camera manager"""
        self.slots_config_path = slots_config_path
        self.cameras_config_path = cameras_config_path
        self.cameras: Dict[str, Dict] = {}
        self.video_captures: Dict[str, cv2.VideoCapture] = {}
        self.frame_locks: Dict[str, threading.Lock] = {}
        self._load_cameras_config()
    
    def _load_cameras_config(self):
        """Load cameras configuration from JSON"""
        if os.path.exists(self.cameras_config_path):
            try:
                with open(self.cameras_config_path, 'r') as f:
                    self.cameras = json.load(f)
                return
            except:
                pass
        
        # Fallback to creating default config
        self.cameras = self._create_default_cameras()
        self._save_cameras_config()
    
    def _create_default_cameras(self) -> Dict[str, Dict]:
        """Create default camera configuration"""
        return {
            "camera_0": {
                "id": "camera_0",
                "name": "Main Entrance",
                "location": "Building A - Ground Floor",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "video_source": "0",  # Webcam
                "status": "active",
                "total_slots": 0
            },
            "camera_1": {
                "id": "camera_1",
                "name": "Back Area",
                "location": "Building A - Basement",
                "latitude": 40.7128,
                "longitude": -74.0061,
                "video_source": "parking_video.mp4",
                "status": "active",
                "total_slots": 0
            }
        }
    
    def _build_cameras_from_videos(self, video_slots_config: Dict) -> Dict[str, Dict]:
        """Build camera configs from video slots config"""
        cameras = {}
        for i, (video_path, slots) in enumerate(video_slots_config.items()):
            camera_id = f"camera_{i}"
            cameras[camera_id] = {
                "id": camera_id,
                "name": f"Camera {i + 1}",
                "location": f"Parking Area {i + 1}",
                "latitude": 40.7128 + (i * 0.0001),
                "longitude": -74.0060 + (i * 0.0001),
                "video_source": video_path,
                "status": "active",
                "total_slots": len(slots) if isinstance(slots, list) else 0
            }
        return cameras
    
    def _save_cameras_config(self):
        """Save cameras configuration to cameras.json"""
        try:
            with open(self.cameras_config_path, 'w') as f:
                json.dump(self.cameras, f, indent=2)
        except Exception as e:
            print(f"Error saving cameras config: {e}")
    
    def get_all_cameras(self) -> List[Dict]:
        """Get all available cameras"""
        return list(self.cameras.values())
    
    def get_camera(self, camera_id: str) -> Optional[Dict]:
        """Get specific camera by ID"""
        return self.cameras.get(camera_id)

    def set_camera_total_slots(self, camera_id: str, total_slots: int) -> None:
        """Persist total slot count for a camera."""
        if camera_id not in self.cameras:
            return
        self.cameras[camera_id]["total_slots"] = int(max(0, total_slots))
        self._save_cameras_config()
    
    def get_nearby_cameras(self, latitude: float, longitude: float, radius_km: float = 5) -> List[Dict]:
        """Get cameras near given coordinates"""
        nearby = []
        for camera in self.cameras.values():
            if camera.get("latitude") and camera.get("longitude"):
                distance = self._calculate_distance(
                    latitude, longitude,
                    camera["latitude"], camera["longitude"]
                )
                if distance <= radius_km:
                    camera_copy = camera.copy()
                    camera_copy["distance_km"] = round(distance, 2)
                    nearby.append(camera_copy)
        
        return sorted(nearby, key=lambda c: c.get("distance_km", float('inf')))
    
    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2) -> float:
        """Calculate distance between two points (simplified)"""
        import math
        # Simplified distance calculation (not accurate)
        return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2) * 111  # approx km
    
    def open_camera_source(self, camera_id: str) -> Optional[cv2.VideoCapture]:
        """Open video capture for camera"""
        camera = self.get_camera(camera_id)
        if not camera:
            return None
        
        source = camera["video_source"]
        
        # Check if it's webcam (numeric)
        try:
            source_int = int(source)
            cap = cv2.VideoCapture(source_int)
            if cap.isOpened():
                self.video_captures[camera_id] = cap
                return cap
            return None
        except ValueError:
            pass
        
        # It's a file path — resolve robustly from cwd, backend/, and project root.
        services_dir = os.path.dirname(os.path.abspath(__file__))            # backend/app/services
        app_dir = os.path.dirname(services_dir)                              # backend/app
        backend_dir = os.path.dirname(app_dir)                               # backend
        project_root = os.path.dirname(backend_dir)                          # project root
        
        # Build list of candidate paths
        candidates = [
            source,                                          # as-is (could be absolute)
            os.path.join(project_root, source),              # relative to project root
            os.path.join(backend_dir, source),               # relative to backend/
            os.path.join(backend_dir, os.path.basename(source)),  # just filename inside backend/
        ]
        
        resolved = None
        for path in candidates:
            if os.path.exists(path):
                resolved = path
                break
        
        if resolved is None:
            print(f"❌ Video file not found for camera '{camera_id}'. Tried: {candidates}")
            return None
        
        print(f"✓ Opening video: {resolved}")
        cap = cv2.VideoCapture(resolved)
        
        if cap.isOpened():
            self.video_captures[camera_id] = cap
            return cap
        
        print(f"❌ cv2.VideoCapture failed to open: {resolved}")
        return None
    
    def close_camera_source(self, camera_id: str):
        """Close video capture for camera"""
        if camera_id in self.video_captures:
            self.video_captures[camera_id].release()
            del self.video_captures[camera_id]
    
    def get_frame(self, camera_id: str) -> Optional[any]:
        """Get current frame from camera - thread-safe"""
        camera = self.get_camera(camera_id)
        if not camera:
            return None
        
        # Create lock if doesn't exist
        if camera_id not in self.frame_locks:
            self.frame_locks[camera_id] = threading.Lock()
        
        # Use lock for thread-safe access
        with self.frame_locks[camera_id]:
            try:
                if camera_id not in self.video_captures:
                    cap = self.open_camera_source(camera_id)
                    if not cap:
                        return None
                else:
                    cap = self.video_captures.get(camera_id)
                
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        return frame
                    else:
                        # Try to reopen (might be end of video)
                        self.close_camera_source(camera_id)
                        cap = self.open_camera_source(camera_id)
                        if cap and cap.isOpened():
                            ret, frame = cap.read()
                            if ret and frame is not None:
                                return frame
            except Exception as e:
                print(f"Error reading frame from {camera_id}: {e}")
                # Close the capture on error
                self.close_camera_source(camera_id)
        
        return None
    
    def load_slots_for_camera(self, camera_id: str) -> List[Dict]:
        """Load slot definitions for camera — matches video_source using basename fallback."""
        camera = self.get_camera(camera_id)
        if not camera:
            return []

        video_source = camera["video_source"]

        if not os.path.exists(self.slots_config_path):
            return []

        try:
            with open(self.slots_config_path, 'r') as f:
                config = json.load(f)

            if not isinstance(config, dict):
                return []

            # 1) Exact key match
            slots = config.get(video_source)
            # 2) Basename match (handles relative vs absolute path mismatch)
            if slots is None:
                video_basename = os.path.basename(video_source)
                for key, val in config.items():
                    if os.path.basename(key) == video_basename and isinstance(val, list) and val:
                        slots = val
                        break
            # 3) Resolved absolute-path match
            if slots is None:
                try:
                    abs_source = os.path.abspath(video_source)
                    slots = config.get(abs_source)
                except Exception:
                    pass

            if isinstance(slots, list):
                for idx, slot in enumerate(slots):
                    if "id" not in slot:
                        slot["id"] = idx + 1
                return slots
        except Exception as e:
            print(f"Error loading slots: {e}")

        return []
    
    # ===== Camera Management (CRUD) Methods =====
    
    def add_camera(
        self, 
        name: str, 
        location: str, 
        video_source: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        total_slots: int = 0,
    ) -> Dict:
        """Add a new camera (CCTV, RTSP, MJPEG, file, or webcam)"""
        # Generate new camera ID
        camera_ids = [int(cid.split('_')[1]) for cid in self.cameras.keys() if cid.startswith('camera_')]
        new_id_num = max(camera_ids) + 1 if camera_ids else 0
        camera_id = f"camera_{new_id_num}"
        
        # Detect camera type and validate
        camera_type = self._detect_camera_type(video_source)
        
        # Create camera record
        camera = {
            "id": camera_id,
            "name": name,
            "location": location,
            "video_source": video_source,
            "status": "active",
            "total_slots": int(max(0, total_slots or 0)),
            "latitude": latitude or 0.0,
            "longitude": longitude or 0.0,
            "username": username,
            "password": password,
            "camera_type": camera_type
        }
        
        self.cameras[camera_id] = camera
        self._save_cameras_config()
        
        return camera
    
    def update_camera(self, camera_id: str, **kwargs) -> Dict:
        """Update camera configuration"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera '{camera_id}' not found")
        
        camera = self.cameras[camera_id]
        
        # Update allowed fields
        allowed_fields = {'name', 'location', 'video_source', 'latitude', 'longitude', 'username', 'password', 'status', 'total_slots'}
        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                if key == 'total_slots':
                    camera[key] = int(max(0, value))
                else:
                    camera[key] = value
        
        # Re-detect camera type if video_source changed
        if 'video_source' in kwargs:
            camera['camera_type'] = self._detect_camera_type(camera['video_source'])
        
        self._save_cameras_config()
        
        return camera
    
    def delete_camera(self, camera_id: str) -> None:
        """Delete a camera"""
        if camera_id not in self.cameras:
            raise ValueError(f"Camera '{camera_id}' not found")
        
        # Close any open capture for this camera
        self.close_camera_source(camera_id)
        
        del self.cameras[camera_id]
        self._save_cameras_config()
    
    def _detect_camera_type(self, video_source: str) -> str:
        """Detect camera type from video source"""
        if video_source.isdigit():
            return "webcam"
        elif video_source.lower().startswith(('rtsp://', 'http://', 'https://', 'rtsps://')):
            if 'rtsp' in video_source.lower():
                return "rtsp"
            else:
                return "http"
        elif video_source.endswith(('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')):
            return "file"
        elif video_source.endswith(('.jpg', '.jpeg', '.png')):
            return "image"
        else:
            return "unknown"
    
    def _build_rtsp_source(self, video_source: str, username: Optional[str], password: Optional[str]) -> str:
        """Build properly formatted RTSP/HTTP URL with authentication"""
        if not username or not password:
            return video_source
        
        # Parse URL
        if '://' not in video_source:
            return video_source
        
        protocol, rest = video_source.split('://', 1)
        
        # Check if credentials already in URL
        if '@' in rest:
            return video_source
        
        # Add credentials
        encoded_user = urllib.parse.quote(username, safe='')
        encoded_pass = urllib.parse.quote(password, safe='')
        
        return f"{protocol}://{encoded_user}:{encoded_pass}@{rest}"
    
    async def test_camera_connection(self, camera_id: str) -> Tuple[bool, str, Dict]:
        """Test camera connectivity and get properties"""
        camera = self.get_camera(camera_id)
        if not camera:
            return False, "Camera not found", {}
        
        video_source = camera['video_source']
        
        # Build proper source with credentials
        source = self._build_rtsp_source(
            video_source,
            camera.get('username'),
            camera.get('password')
        )
        
        try:
            # Try to open camera
            cap = None
            try:
                # Try as integer (webcam)
                if video_source.isdigit():
                    cap = cv2.VideoCapture(int(video_source))
                else:
                    # Try as file/URL/RTSP
                    cap = cv2.VideoCapture(source)
            except:
                cap = cv2.VideoCapture(source)
            
            if not cap or not cap.isOpened():
                return False, f"Cannot access camera source: {camera['camera_type']}", {}
            
            # Try to read a frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                return False, "Camera is accessible but cannot read frames", {}
            
            # Get properties
            cap = cv2.VideoCapture(source)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            cap.release()
            
            props = {
                'width': width,
                'height': height,
                'fps': fps if fps > 0 else 30,
                'frame_count': frame_count
            }
            
            return True, f"✓ Camera connected successfully ({width}x{height} @ {props['fps']:.1f} fps)", props
        
        except Exception as e:
            return False, f"Error: {str(e)}", {}
