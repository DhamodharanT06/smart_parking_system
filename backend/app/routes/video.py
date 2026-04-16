from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from typing import Optional
import os

router = APIRouter(prefix="/api/video", tags=["video"])


@router.get("/trail/{video_name}")
async def get_trail_video(video_name: str):
    """Stream trail video for testing model performance"""
    
    # Security: only allow video files from current directory
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    
    if not any(video_name.lower().endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    video_path = os.path.join("videos", video_name)
    
    if not os.path.exists(video_path):
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        headers={"Content-Disposition": f"inline; filename={video_name}"}
    )


@router.get("/trail/list")
async def list_trail_videos():
    """List available trail videos"""
    videos_dir = "videos"
    
    if not os.path.exists(videos_dir):
        return {"videos": []}
    
    allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv']
    videos = []
    
    for file in os.listdir(videos_dir):
        if any(file.lower().endswith(ext) for ext in allowed_extensions):
            file_path = os.path.join(videos_dir, file)
            file_size = os.path.getsize(file_path)
            videos.append({
                "name": file,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "path": f"/api/video/trail/{file}"
            })
    
    return {"videos": videos, "total": len(videos)}
