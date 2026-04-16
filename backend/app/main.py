from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os
import traceback
import cv2
import threading

# Disable OpenCV threading to prevent FFmpeg threading issues
cv2.setNumThreads(0)

# Configure FFmpeg threading
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'

from app.config import CORS_ORIGINS, HOST, PORT, MODEL_PATH, SLOTS_FILE
from app.routes import cameras, parking, video
from app.services.camera_manager import CameraManager
from app.services.detector import ParkingDetector

# Create FastAPI app
app = FastAPI(
    title="Smart Parking System",
    description="Real-time parking detection system with YOLO",
    version="1.0.0"
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions"""
    error_detail = str(exc)
    error_type = type(exc).__name__
    
    # Log the full error
    print(f"ERROR [{error_type}]: {error_detail}")
    print(traceback.format_exc())
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": f"Internal server error: {error_detail}",
            "error_type": error_type,
            "path": str(request.url)
        }
    )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    # Initialize camera manager with both config files
    # cameras.json should be in backend folder (same level as app folder)
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cameras_config = os.path.join(backend_dir, 'cameras.json')
    
    camera_manager = CameraManager(
        slots_config_path=SLOTS_FILE, 
        cameras_config_path=cameras_config
    )
    cameras.init_camera_manager(SLOTS_FILE, camera_manager)
    
    print(f"\n✓ Backend initialized successfully:")
    print(f"  - Project root: {os.path.dirname(backend_dir)}")
    print(f"  - YOLO Model: {MODEL_PATH}")
    print(f"  - Cameras Config: {cameras_config}")
    print(f"  - Slots Config: {SLOTS_FILE}\n")
    
    detector = ParkingDetector(MODEL_PATH, confidence=0.2)
    parking.init_parking_services(camera_manager, detector)
    
    print(f"✓ YOLO Model loaded successfully")
    print(f"✓ All services initialized\n")
except Exception as e:
    print(f"\n❌ Error initializing services: {e}")
    import traceback
    traceback.print_exc()
    print()

# Include routes
app.include_router(cameras.router)
app.include_router(parking.router)
app.include_router(video.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Parking System API",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": "/api"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=True
    )
