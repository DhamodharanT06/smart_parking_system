from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
import cv2
import asyncio
from app.models.schemas import Camera
from app.services.camera_manager import CameraManager

router = APIRouter(prefix="/api/cameras", tags=["cameras"])

# Global camera manager
camera_manager = None


def init_camera_manager(slots_config_path: str, camera_mgr: Optional[CameraManager] = None):
    global camera_manager
    camera_manager = camera_mgr if camera_mgr is not None else CameraManager(slots_config_path)


# Pydantic models for requests/responses
class CameraAddRequest(BaseModel):
    """Request model for adding a camera"""
    name: str
    location: str
    video_source: str  # URL, IP camera RTSP, webcam ID, or file path
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    username: Optional[str] = None
    password: Optional[str] = None
    total_slots: int = 0


class CameraUpdateRequest(BaseModel):
    """Request model for updating a camera"""
    name: Optional[str] = None
    location: Optional[str] = None
    video_source: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    username: Optional[str] = None
    password: Optional[str] = None
    total_slots: Optional[int] = None


class CameraTestResponse(BaseModel):
    """Response for camera connectivity test"""
    camera_id: str
    camera_name: str
    is_accessible: bool
    message: str
    frame_width: Optional[int] = None
    frame_height: Optional[int] = None
    fps: Optional[float] = None


# ─── In-memory favorites store ───────────────────────────────────────────────
_favorites: set = set()


@router.get("/", response_model=List[Camera])
async def list_cameras():
    """Get all available cameras"""
    try:
        if not camera_manager:
            raise HTTPException(
                status_code=500, 
                detail="Camera manager not initialized. Please restart the server."
            )
        
        cameras = camera_manager.get_all_cameras()
        return [Camera(**cam) for cam in cameras]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving cameras: {str(e)}"
        )


@router.get("/favorites", response_model=List[Camera])
async def get_favorites():
    """Get all favorited cameras"""
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    result = []
    for cid in list(_favorites):
        cam = camera_manager.get_camera(cid)
        if cam:
            result.append(Camera(**cam))
    return result


@router.get("/nearby", response_model=List[Camera])
async def get_nearby_cameras(
    latitude: float = 40.7128,
    longitude: float = -74.0060,
    radius: float = 5
):
    """Get cameras near given coordinates (radius in km)"""
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    cameras = camera_manager.get_nearby_cameras(latitude, longitude, radius)
    return [Camera(**cam) for cam in cameras]


@router.get("/{camera_id}", response_model=Camera)
async def get_camera(camera_id: str):
    """Get specific camera details"""
    try:
        if not camera_manager:
            raise HTTPException(
                status_code=500, 
                detail="Camera manager not initialized. Please restart the server."
            )
        
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(
                status_code=404, 
                detail=f"Camera with ID '{camera_id}' not found"
            )
        
        return Camera(**camera)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving camera details: {str(e)}"
        )


@router.post("/", response_model=Camera)
async def add_camera(req: CameraAddRequest):
    """Add a new camera (CCTV, IP camera, webcam, or video file)"""
    try:
        if not camera_manager:
            raise HTTPException(status_code=500, detail="Camera manager not initialized")
        
        camera = camera_manager.add_camera(
            name=req.name,
            location=req.location,
            video_source=req.video_source,
            latitude=req.latitude,
            longitude=req.longitude,
            username=req.username,
            password=req.password,
            total_slots=req.total_slots,
        )
        
        return Camera(**camera)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error adding camera: {str(e)}"
        )


@router.put("/{camera_id}", response_model=Camera)
async def update_camera(camera_id: str, req: CameraUpdateRequest):
    """Update an existing camera configuration"""
    try:
        if not camera_manager:
            raise HTTPException(status_code=500, detail="Camera manager not initialized")
        
        camera = camera_manager.update_camera(camera_id, **req.dict(exclude_unset=True))
        
        return Camera(**camera)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error updating camera: {str(e)}"
        )


@router.delete("/{camera_id}")
async def delete_camera(camera_id: str):
    """Delete a camera"""
    try:
        if not camera_manager:
            raise HTTPException(status_code=500, detail="Camera manager not initialized")
        
        camera_manager.delete_camera(camera_id)
        return {"message": f"Camera '{camera_id}' deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error deleting camera: {str(e)}"
        )


@router.post("/{camera_id}/test", response_model=CameraTestResponse)
async def test_camera_connectivity(camera_id: str):
    """Test if a camera is accessible and can provide frames"""
    try:
        if not camera_manager:
            raise HTTPException(status_code=500, detail="Camera manager not initialized")
        
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
        
        # Test camera connection in background
        is_accessible, message, props = await camera_manager.test_camera_connection(camera_id)
        
        return CameraTestResponse(
            camera_id=camera_id,
            camera_name=camera['name'],
            is_accessible=is_accessible,
            message=message,
            frame_width=props.get('width'),
            frame_height=props.get('height'),
            fps=props.get('fps')
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error testing camera: {str(e)}"
        )


@router.post("/{camera_id}/favorite")
async def add_favorite(camera_id: str):
    """Add a camera to favorites"""
    if not camera_manager:
        raise HTTPException(status_code=500, detail="Camera manager not initialized")
    if not camera_manager.get_camera(camera_id):
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")
    _favorites.add(camera_id)
    return {"message": f"Camera '{camera_id}' added to favorites", "favorites": list(_favorites)}


@router.delete("/{camera_id}/favorite")
async def remove_favorite(camera_id: str):
    """Remove a camera from favorites"""
    _favorites.discard(camera_id)
    return {"message": f"Camera '{camera_id}' removed from favorites", "favorites": list(_favorites)}
