# Smart Parking System Backend

This is the FastAPI backend for the Smart Parking System.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server:
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

## API Endpoints

### Cameras
- `GET /api/cameras/` - List all cameras
- `GET /api/cameras/{camera_id}` - Get camera details
- `GET /api/cameras/nearby` - Get nearby cameras

### Parking Status
- `GET /api/parking/{camera_id}/status` - Get parking status
- `GET /api/parking/{camera_id}/stream` - Stream video with detection
- `GET /api/parking/{camera_id}/statistics` - Get statistics

### Video
- `GET /api/video/trail/list` - List available trail videos
- `GET /api/video/trail/{video_name}` - Stream trail video
