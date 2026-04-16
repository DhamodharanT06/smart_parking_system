"# 🚗 Smart Parking System - Professional Web Application

A complete, production-ready web application for real-time parking detection using YOLOv8, FastAPI, and React.

## ✨ Features

✅ **Real-time Parking Detection** - AI-powered vehicle detection using YOLOv8
✅ **Camera Management** - Select from multiple CCTV cameras  
✅ **Live Dashboard** - Beautiful UI showing occupancy statistics
✅ **Visual Slot Grid** - Color-coded parking slot status (Green=Available, Red=Occupied)
✅ **Live Stream** - Real-time video with detection overlay
✅ **Trail View** - Test model performance with recorded videos
✅ **Responsive Design** - Works on desktop, tablet, mobile
✅ **REST API** - Full-featured API with interactive docs
✅ **Easy to Deploy** - Docker-ready, cloud-compatible

---

## 🏗️ Architecture

```
Frontend (React)          Backend (FastAPI)          Data & ML
┌──────────────────┐     ┌──────────────────┐      ┌──────────┐
│ Dashboard        │────→│ REST API         │────→ │ YOLOv8   │
│ Camera Select    │     │ Camera Manager   │      │ Model    │
│ Slot Grid        │     │ Parking Detection│      │ Detector │
│ Live Stream      │     │ Video Streaming  │      │          │
│ Trail View       │     │ Authentication   │      │          │
└──────────────────┘     └──────────────────┘      └──────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- ~2GB free disk space (for models)

### 1. Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python -m app.main
```

**Backend runs at**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd frontend
npm install
npm start
```

**Frontend runs at**: http://localhost:3000

### 3. Access Application

Open: **http://localhost:3000**

Select a camera → View parking status → Done! ✅

---

## 📁 Project Structure

```
smart-parking-webapp/
├── backend/                          # FastAPI backend
│   ├── app/
│   │   ├── main.py                 # Entry point
│   │   ├── config.py               # Configuration
│   │   ├── models/schemas.py       # Data models
│   │   ├── routes/                 # API endpoints
│   │   │   ├── cameras.py
│   │   │   ├── parking.py
│   │   │   └── video.py
│   │   ├── services/               # Business logic
│   │   │   ├── detector.py
│   │   │   └── camera_manager.py
│   │   └── utils/                  # Utilities
│   ├── slots.json                  # Parking slots config
│   ├── yolov8n.pt                 # YOLO model
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                         # React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── CameraSelector.jsx
│   │   │   ├── ParkingDashboard.jsx
│   │   │   ├── SlotGrid.jsx
│   │   │   └── VideoStream.jsx
│   │   ├── pages/
│   │   │   ├── Home.jsx
│   │   │   └── TrailView.jsx
│   │   ├── services/api.js
│   │   ├── App.jsx
│   │   └── index.jsx
│   ├── package.json
│   └── README.md
│
├── QUICKSTART.md                     # ⭐ Start here!
├── SETUP.md                          # Detailed setup guide
├── API_GUIDE.md                      # API documentation
├── LEARNING_GUIDE.md                 # Learn & master
└── README.md                         # This file
```

---

## 📡 API Endpoints

### Cameras
```
GET  /api/cameras/              → List all cameras
GET  /api/cameras/{id}          → Get camera details
GET  /api/cameras/nearby        → Get nearby cameras
```

### Parking Status
```
GET  /api/parking/{id}/status        → Real-time status
GET  /api/parking/{id}/stream        → Live video stream
GET  /api/parking/{id}/statistics    → Parking statistics
```

### Video
```
GET  /api/video/trail/list           → List test videos
GET  /api/video/trail/{name}         → Stream video
```

**Full API docs**: http://localhost:8000/docs

---

## 🎯 How to Use

### 1. Select Camera
Click on camera in left sidebar to choose which parking area to monitor.

### 2. View Dashboard
See real-time statistics:
- Total parking slots
- Available slots
- Occupied slots
- Occupancy percentage

### 3. Check Slot Grid
Visual grid showing each parking slot:
- 🟢 Green = Available
- 🔴 Red = Occupied

### 4. Watch Live Stream
Real-time video feed with AI detection overlay showing vehicle locations.

### 5. Test with Videos
Go to "Trail View" tab to upload and test model performance on recorded videos.

---

## ⚙️ Configuration

### Add New Camera

1. Edit `backend/slots.json`:
```json
{
  "camera_name.mp4": [
    {"id": 0, "x": 10, "y": 20, "width": 50, "height": 50},
    {"id": 1, "x": 70, "y": 20, "width": 50, "height": 50}
  ]
}
```

2. Restart backend
3. Camera appears automatically in dashboard

### Change Detection Confidence
In `backend/app/config.py`:
```python
CONFIDENCE_THRESHOLD = 0.3  # Range: 0.1 - 0.9
```

### Customize UI Colors
Edit CSS files in `frontend/src/components/*.css`

---

## 🧠 Learning Resources

- **Complete Setup Guide**: Read [SETUP.md](SETUP.md)
- **Master the API**: Read [API_GUIDE.md](API_GUIDE.md)
- **Learn & Build**: Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md)
- **Quick Reference**: Read [QUICKSTART.md](QUICKSTART.md)

---

## 🐛 Troubleshooting

### Backend won't start
```bash
pip install --upgrade -r requirements.txt
python -m app.main
```

### Frontend can't connect
- Check API URL: `frontend/.env` should have `REACT_APP_API_URL=http://localhost:8000/api`
- Restart frontend: `npm start`

### No video showing
- Ensure camera video file exists
- Check `slots.json` has correct coordinates
- Verify YOLO model file exists

### Port already in use
```bash
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /PID [PID] /F
```

For more help: See [QUICKSTART.md](QUICKSTART.md#-troubleshooting-quick-fixes)

---

## 🚀 Deployment

### Docker (Recommended)
```bash
docker-compose up
```

### Cloud Platforms
- ✅ AWS EC2
- ✅ Google Cloud Platform
- ✅ Heroku
- ✅ DigitalOcean

### Production Checklist
- [ ] Set `DEBUG=False`
- [ ] Configure HTTPS/SSL
- [ ] Set up database
- [ ] Configure authentication
- [ ] Monitor performance
- [ ] Set up logging & alerts

---

## 🔧 Key Technologies

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI, Python 3.10 |
| Frontend | React 18, JavaScript |
| ML Model | YOLOv8 (Ultralytics) |
| Computer Vision | OpenCV |
| Video Streaming | MJPEG |
| HTTP Server | Uvicorn |
| API Format | REST + JSON |

---

## 📊 Example Response

```json
{
  "camera_id": "camera_0",
  "camera_name": "Main Entrance",
  "timestamp": "2026-01-31T15:30:45",
  "total_slots": 15,
  "occupied_slots": 10,
  "available_slots": 5,
  "occupancy_rate": 66.67,
  "slots": [
    {"id": 0, "status": "available", "x": 10, "y": 20},
    {"id": 1, "status": "occupied", "x": 70, "y": 20}
  ]
}
```

---

## 🎓 Learning Path

**Week 1**: Setup & Basics
- Day 1-2: Complete SETUP.md
- Day 3-4: Read API_GUIDE.md
- Day 5: Customize UI

**Week 2**: Development
- Day 1-2: Follow LEARNING_GUIDE.md
- Day 3-5: Add new features

**Week 3**: Deployment
- Day 1-2: Containerize
- Day 3-5: Deploy to cloud

---

## ⭐ Quick Links

- 📖 **START HERE**: [QUICKSTART.md](QUICKSTART.md)
- 📋 **Full Setup**: [SETUP.md](SETUP.md)
- 📡 **API Reference**: [API_GUIDE.md](API_GUIDE.md)
- 🎓 **Learning Guide**: [LEARNING_GUIDE.md](LEARNING_GUIDE.md)

---

## 💡 Next Steps

1. ✅ **Run the application** (10 min)
2. ✅ **Select a camera** (1 min)
3. ✅ **View parking status** (1 min)
4. ✅ **Read documentation** (30 min)
5. ✅ **Customize for your needs** (depends)
6. ✅ **Deploy to production** (depends)

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Report issues
- Suggest features
- Submit pull requests
- Improve documentation

---

## 📝 License

Open source - use freely for education, research, and commercial projects.

---

## 📞 Support

- Check [QUICKSTART.md](QUICKSTART.md) for common issues
- Read [API_GUIDE.md](API_GUIDE.md) for API questions
- Review [LEARNING_GUIDE.md](LEARNING_GUIDE.md) to learn

---

## 🎉 You're Ready!

Everything is set up and ready to use. Start with:

```bash
# Terminal 1
cd backend && python -m app.main

# Terminal 2
cd frontend && npm start

# Open browser
http://localhost:3000
```

**Happy Parking! 🚗**

---

**Last Updated**: January 31, 2026
**Version**: 1.0.0
**Status**: Production Ready ✅" 
