from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class SlotStatus(str, Enum):
    """Parking slot status"""
    FREE = "free"
    OCCUPIED = "occupied"
    PARTIAL = "partial"
    # Legacy value for backward compatibility
    AVAILABLE = "available"
    UNKNOWN = "unknown"


class ParkingSlot(BaseModel):
    """Single parking slot"""
    id: int
    x: int
    y: int
    width: int
    height: int
    status: SlotStatus = SlotStatus.UNKNOWN


class Camera(BaseModel):
    """Camera information"""
    id: str
    name: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    video_source: str  # File path or RTSP URL
    status: str = "active"
    total_slots: int = 0
    camera_type: Optional[str] = None


class ParkingStatus(BaseModel):
    """Real-time parking status"""
    camera_id: str
    camera_name: str
    timestamp: str
    total_slots: int
    available_slots: int
    occupied_slots: int
    partial_slots: int = 0
    occupancy_rate: float  # percentage 0-100
    slots: List[ParkingSlot]


class DetectionResult(BaseModel):
    """Detection result from model"""
    slot_id: int
    confidence: float
    status: SlotStatus


class VideoStreamResponse(BaseModel):
    """Video stream metadata"""
    camera_id: str
    fps: int
    resolution: str
    encoding: str = "MJPEG"
