from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import cv2
from app.models.schemas import ParkingStatus, SlotStatus, ParkingSlot
from app.services.camera_manager import CameraManager
from app.services.detector import ParkingDetector, SlotAnalyzer, VEHICLE_CLASSES
from app.services.slot_calibrator import SlotCalibrator
from app.utils.video_handler import VideoStreamHandler
from datetime import datetime
from typing import Optional
import os

router = APIRouter(prefix="/api/parking", tags=["parking"])

# Global managers
camera_manager = None
detector = None
stream_handler = None


def init_parking_services(camera_mgr: CameraManager, detector_model: ParkingDetector):
    global camera_manager, detector, stream_handler
    camera_manager = camera_mgr
    detector = detector_model
    stream_handler = VideoStreamHandler()


# ─── Color palette (BGR) ────────────────────────────────────────────────────
_COLORS = [
    (56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255),
    (49, 210, 207), (10, 249, 72),  (23, 204, 146), (134, 219, 61),
    (52, 147,  26), (187, 212,  0), (168, 153,  44), (255, 194,  0),
    (147,  69,  52), (255, 113,  0), (0, 121, 255),  (255,  49, 197),
]

# Slot status colors (BGR)
_SLOT_COLORS = {
    "free": (30, 30, 220),     # red
    "partial": (0, 160, 255),  # yellow/orange
    "occupied": (0, 220, 60),  # green
}


def _resolve_video_source(source: str) -> Optional[str]:
    """Resolve video — webcam index or file path (relative to both project root and backend/)"""
    try:
        int(source)
        return source
    except (ValueError, TypeError):
        pass
    if not source:
        return None
    # RTSP / HTTP URL → return as-is
    if source.lower().startswith(('rtsp://', 'rtsps://', 'http://', 'https://')):
        return source
    # __file__ is backend/app/routes/parking.py
    # 1 dirname = backend/app/routes, 2 = backend/app, 3 = backend, 4 = project root
    _routes_dir   = os.path.dirname(os.path.abspath(__file__))
    _backend_dir  = os.path.dirname(os.path.dirname(_routes_dir))   # backend/
    _project_root = os.path.dirname(_backend_dir)                   # Smart Parking System/
    candidates = [
        source,
        os.path.join(_project_root, source),
        os.path.join(_backend_dir, source),
        os.path.join(_backend_dir, os.path.basename(source)),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    print(f"❌ Video not found. Tried: {candidates}")
    return None


def _open_cap(source: str) -> Optional[cv2.VideoCapture]:
    try:
        return cv2.VideoCapture(int(source))
    except (ValueError, TypeError):
        return cv2.VideoCapture(source)


def _draw_yolo_on_frame(frame, detections) -> tuple:
    """Draw YOLO vehicle detections — same style as debug_frame_root.jpg. Returns (annotated, count)."""
    frame = frame.copy()
    names = detections.names if hasattr(detections, 'names') else {}
    count = 0
    if detections.boxes is not None:
        for box in detections.boxes:
            cls_id = int(box.cls[0])
            label = names.get(cls_id, str(cls_id))
            if label.lower() not in VEHICLE_CLASSES:
                continue
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            count += 1
            color = _COLORS[cls_id % len(_COLORS)]
            text = f"{label} {conf:.2f}"
            (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
            cv2.putText(frame, text, (x1 + 2, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
    # Banner
    banner = f"Vehicles Detected: {count}"
    (bw, bh), _ = cv2.getTextSize(banner, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
    cv2.rectangle(frame, (0, 0), (bw + 20, bh + 18), (0, 0, 0), -1)
    cv2.putText(frame, banner, (10, bh + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 230, 80), 2)
    return frame, count


def _draw_slots_on_frame(frame, slots_with_status: list, stats: dict) -> any:
    """Draw colored slot boxes + legend on frame."""
    out = frame.copy()
    for slot in slots_with_status:
        x = slot.get("x", 0)
        y = slot.get("y", 0)
        w = slot.get("width", 0)
        h = slot.get("height", 0)
        if w == 0 or h == 0:
            continue
        status = slot.get("status", "free")
        color = _SLOT_COLORS.get(status, (128, 128, 128))
        cv2.rectangle(out, (x, y), (x + w, y + h), color, 2)
        label = f"#{slot['id']}"
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
        cv2.rectangle(out, (x, y - th - 5), (x + tw + 4, y), color, -1)
        cv2.putText(out, label, (x + 2, y - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
    # Summary banner bottom-left
    h_fr = out.shape[0]
    lines = [
        f"Total: {stats.get('total_slots', 0)}",
        f"Free: {stats.get('available_slots', 0)}",
        f"Partial: {stats.get('partial_slots', 0)}",
        f"Occupied: {stats.get('occupied_slots', 0)}",
    ]
    colors_bar = [(200, 200, 200), _SLOT_COLORS["free"], _SLOT_COLORS["partial"], _SLOT_COLORS["occupied"]]
    bar_h = 22
    y0 = h_fr - bar_h * len(lines) - 8
    cv2.rectangle(out, (0, y0 - 4), (200, h_fr), (0, 0, 0), -1)
    for i, (line, col) in enumerate(zip(lines, colors_bar)):
        cv2.putText(out, line, (8, y0 + bar_h * i + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 1)
    return out


# ─── Status endpoint ─────────────────────────────────────────────────────────

@router.get("/{camera_id}/status", response_model=ParkingStatus)
async def get_parking_status(camera_id: str, status_mode: str = Query("slot")):
    """Get real-time parking status with available / partial / occupied breakdown"""
    try:
        if not camera_manager or not detector:
            raise HTTPException(status_code=500, detail="Services not initialized.")

        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

        use_vehicle_mode = str(status_mode).strip().lower() == "vehicle"

        configured_slots = camera_manager.load_slots_for_camera(camera_id)
        has_real_slots = bool(configured_slots)
        registered_total = int(max(0, camera.get("total_slots", 0) or 0))
        base_capacity = len(configured_slots) if has_real_slots else 12
        total_capacity = registered_total if registered_total > 0 else base_capacity

        frame = camera_manager.get_frame(camera_id)
        if frame is None:
            raw_source = camera.get("video_source", "")
            resolved = _resolve_video_source(raw_source)
            if resolved:
                cap = _open_cap(resolved)
                if cap and cap.isOpened():
                    ret, frame = cap.read()
                    cap.release()
                    if not ret:
                        frame = None

        occupied = 0
        partial  = 0
        parking_slots = []

        vehicle_count = 0

        if frame is not None and has_real_slots:
            # Apply brightness normalization (per paper)
            frame = stream_handler.normalize_brightness(frame)
            
            # Use IoU-based slot detection
            result = detector.detect_slots(frame, configured_slots)
            vehicle_count = int(result.get("vehicle_count", 0))

            if use_vehicle_mode:
                occupied = min(vehicle_count, total_capacity)
                partial = 0
                available = max(0, total_capacity - occupied)
                parking_slots = [
                    ParkingSlot(
                        id=i,
                        x=0,
                        y=0,
                        width=0,
                        height=0,
                        status=SlotStatus("occupied" if i <= occupied else "free"),
                    )
                    for i in range(1, total_capacity + 1)
                ]
            else:
                stats  = SlotAnalyzer.calculate_statistics(result["slots"])
                occupied  = min(stats["occupied_slots"], total_capacity)
                partial   = min(stats["partial_slots"], max(0, total_capacity - occupied))
                available = max(0, total_capacity - occupied - partial)
                parking_slots = [
                    ParkingSlot(
                        id=s["id"], x=s["x"], y=s["y"],
                        width=s["width"], height=s["height"],
                        status=SlotStatus(s["status"])
                    )
                    for s in result["slots"]
                ]
                if len(parking_slots) < total_capacity:
                    parking_slots.extend([
                        ParkingSlot(
                            id=i,
                            x=0,
                            y=0,
                            width=0,
                            height=0,
                            status=SlotStatus("free"),
                        )
                        for i in range(len(parking_slots) + 1, total_capacity + 1)
                    ])
                elif len(parking_slots) > total_capacity:
                    parking_slots = parking_slots[:total_capacity]
        else:
            # Fallback: count vehicles with YOLO
            if frame is not None:
                try:
                    with detector.detection_lock:
                        results = detector.model(frame, conf=detector.confidence, verbose=False)
                    det = results[0]
                    if det.boxes is not None and det.names:
                        for box in det.boxes:
                            lbl = det.names.get(int(box.cls[0]), "")
                            if lbl.lower() in VEHICLE_CLASSES:
                                vehicle_count += 1
                except Exception as e:
                    print(f"Detection error: {e}")

            occupied  = min(vehicle_count, total_capacity)
            partial   = 0
            available = total_capacity - occupied
            for i in range(1, total_capacity + 1):
                st = "occupied" if i <= occupied else "free"
                parking_slots.append(
                    ParkingSlot(id=i, x=0, y=0, width=0, height=0, status=SlotStatus(st))
                )
        occupancy_rate = ((occupied + partial) / total_capacity * 100) if total_capacity > 0 else 0

        return ParkingStatus(
            camera_id=camera_id,
            camera_name=camera["name"],
            timestamp=datetime.now().isoformat(),
            total_slots=total_capacity,
            available_slots=available,
            occupied_slots=occupied,
            partial_slots=partial,
            occupancy_rate=occupancy_rate,
            slots=parking_slots,
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing parking status: {str(e)}")


# ─── Streaming endpoint ───────────────────────────────────────────────────────

@router.get("/{camera_id}/stream")
async def get_parking_stream(camera_id: str, overlay_slots: bool = Query(True)):
    """MJPEG stream with YOLO bounding boxes + colored slot overlay"""
    if not camera_manager or not detector:
        raise HTTPException(status_code=500, detail="Services not initialized.")

    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    raw_source = camera["video_source"]
    resolved = _resolve_video_source(raw_source)
    if resolved is None:
        raise HTTPException(status_code=503, detail=f"Video not found: {raw_source}")

    configured_slots = camera_manager.load_slots_for_camera(camera_id)

    def frame_generator():
        cap = _open_cap(resolved)
        if not cap or not cap.isOpened():
            return

        frame_count = 0
        last_dets = None
        last_slot_result = None
        YOLO_EVERY = 3

        while True:
            ret, frame = cap.read()
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break

            # Apply brightness normalization (per paper)
            frame = stream_handler.normalize_brightness(frame)

            if frame_count % YOLO_EVERY == 0:
                try:
                    with detector.detection_lock:
                        results = detector.model(frame, conf=detector.confidence, verbose=False)
                    last_dets = results[0]
                    if overlay_slots and configured_slots:
                        last_slot_result = detector.detect_slots(frame, configured_slots)
                except Exception as e:
                    print(f"Detection error: {e}")

            # Draw YOLO boxes (style matching debug_frame_root.jpg)
            if last_dets is not None:
                annotated, _ = _draw_yolo_on_frame(frame, last_dets)
            else:
                annotated = frame.copy()

            # Overlay slot boxes if slots are configured
            if overlay_slots and configured_slots and last_slot_result:
                stats = SlotAnalyzer.calculate_statistics(last_slot_result["slots"])
                annotated = _draw_slots_on_frame(annotated, last_slot_result["slots"], stats)

            yield annotated
            frame_count += 1
            if frame_count > 90000:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                frame_count = 0

        cap.release()

    return StreamingResponse(
        stream_handler.generate_mjpeg_stream(frame_generator()),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# ─── Single frame endpoint ────────────────────────────────────────────────────

@router.get("/{camera_id}/frame")
async def get_parking_frame(camera_id: str, overlay_slots: bool = Query(True)):
    """Return single JPEG: YOLO bounding boxes + slot overlay"""
    if not camera_manager or not detector:
        raise HTTPException(status_code=500, detail="Services not initialized.")

    camera = camera_manager.get_camera(camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail=f"Camera '{camera_id}' not found")

    raw_source = camera["video_source"]
    resolved = _resolve_video_source(raw_source)
    if resolved is None:
        raise HTTPException(status_code=503, detail=f"Video not found: {raw_source}")

    cap = _open_cap(resolved)
    if not cap or not cap.isOpened():
        raise HTTPException(status_code=503, detail="Cannot open video source")

    ret, frame = cap.read()
    cap.release()
    if not ret or frame is None:
        raise HTTPException(status_code=503, detail="No frame available")

    try:
        # Apply brightness normalization (per paper)
        frame = stream_handler.normalize_brightness(frame)
        
        with detector.detection_lock:
            results = detector.model(frame, conf=detector.confidence, verbose=False)
        annotated, _count = _draw_yolo_on_frame(frame, results[0])

        configured_slots = camera_manager.load_slots_for_camera(camera_id)
        if overlay_slots and configured_slots:
            slot_result = detector.detect_slots(frame, configured_slots)
            stats = SlotAnalyzer.calculate_statistics(slot_result["slots"])
            annotated = _draw_slots_on_frame(annotated, slot_result["slots"], stats)
    except Exception as e:
        print(f"Detection error: {e}")
        annotated = frame

    stream_handler.save_debug_frame(annotated, camera_id)
    ret, jpeg = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
    if not ret:
        raise HTTPException(status_code=500, detail="Failed to encode frame")

    return StreamingResponse(iter([jpeg.tobytes()]), media_type="image/jpeg")


# ─── Statistics endpoint ──────────────────────────────────────────────────────

@router.get("/{camera_id}/statistics")
async def get_parking_statistics(camera_id: str):
    """Get parking statistics summary"""
    status = await get_parking_status(camera_id)
    total = status.total_slots
    return {
        "camera_id":          camera_id,
        "camera_name":        status.camera_name,
        "timestamp":          status.timestamp,
        "total_slots":        total,
        "available_slots":    status.available_slots,
        "partial_slots":      status.partial_slots,
        "occupied_slots":     status.occupied_slots,
        "occupancy_rate":     round(status.occupancy_rate, 2),
        "available_percentage": round(status.available_slots / total * 100, 2) if total > 0 else 0,
    }


@router.post("/{camera_id}/calibrate-slots")
async def calibrate_parking_slots(
    camera_id: str,
    sample_frames: int = 8,
    min_support_frames: int = 2,
    target_slots: int = 0,
):
    """Auto-calibrate slot coordinates from multiple sampled frames and save debug_frame_root.jpg."""
    if not camera_manager or not detector or not stream_handler:
        raise HTTPException(status_code=500, detail="Services not initialized.")

    sample_frames = max(2, min(30, int(sample_frames)))
    min_support_frames = max(2, min(10, int(min_support_frames)))
    target_slots = max(0, min(200, int(target_slots)))

    try:
        result = SlotCalibrator.calibrate_from_camera(
            camera_manager=camera_manager,
            detector=detector,
            stream_handler=stream_handler,
            camera_id=camera_id,
            sample_frames=sample_frames,
            min_support_frames=min_support_frames,
            target_slots=target_slots,
        )
        return {
            "message": "Slot calibration completed",
            **result,
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calibration failed: {str(e)}")

