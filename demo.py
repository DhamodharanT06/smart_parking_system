"""
Smart Parking System — Standalone Demo
Run from the project root:   python demo.py

Shows live YOLO vehicle detection on parking_test_video.mp4 in a window.
Press  Q  to quit at any time.
"""

import cv2
import os
from ultralytics import YOLO

# ── Config ────────────────────────────────────────────────────────────────────
VIDEO_FILE     = "parking_test_video.mp4"
MODEL_FILE     = "yolov8n.pt"
CONFIDENCE     = 0.2
VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle", "bicycle"}
YOLO_EVERY     = 3       # run YOLO every N frames (keeps display smooth)
WINDOW_TITLE   = "Smart Parking System — Live Detection  |  Press Q to quit"

# Colors per class id (BGR)
_COLORS = [
    (56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255),
    (49, 210, 207), (10, 249, 72),  (23, 204, 146), (134, 219, 61),
    (52, 147,  26), (187, 212,  0), (168, 153,  44), (255, 194,  0),
    (147,  69,  52), (255, 113,  0), (0, 121, 255), (255,  49, 197),
]
# ─────────────────────────────────────────────────────────────────────────────


def draw_detections(frame, results):
    """Draw bounding boxes + banner on frame (vehicle classes only)."""
    names  = results.names if hasattr(results, "names") else {}
    count  = 0
    boxes  = results.boxes if results.boxes is not None else []

    for box in boxes:
        cls_id = int(box.cls[0])
        label  = names.get(cls_id, str(cls_id))
        if label.lower() not in VEHICLE_CLASSES:
            continue
        count += 1
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf  = float(box.conf[0])
        color = _COLORS[cls_id % len(_COLORS)]

        # Filled label background
        txt = f"{label} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, txt, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    # Top-left banner
    banner = f"Vehicles Detected: {count}"
    (bw, bh), _ = cv2.getTextSize(banner, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
    cv2.rectangle(frame, (0, 0), (bw + 20, bh + 18), (0, 0, 0), -1)
    cv2.putText(frame, banner, (10, bh + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 230, 80), 2)
    return frame, count


def main():
    # ── Resolve video path ──────────────────────────────────────────────────
    script_dir = os.path.dirname(os.path.abspath(__file__))
    video_path = os.path.join(script_dir, VIDEO_FILE)
    if not os.path.exists(video_path):
        # also try backend/ subfolder
        alt = os.path.join(script_dir, "backend", VIDEO_FILE)
        if os.path.exists(alt):
            video_path = alt
        else:
            print(f"❌  Video not found: {VIDEO_FILE}")
            print(f"    Looked in: {video_path}")
            print(f"    Also tried: {alt}")
            return

    model_path = os.path.join(script_dir, MODEL_FILE)
    if not os.path.exists(model_path):
        print(f"❌  Model not found: {model_path}")
        return

    print(f"\n🎥  Video : {video_path}")
    print(f"🤖  Model : {model_path}")
    print(f"🎯  Conf  : {CONFIDENCE}")
    print(f"\n{'─'*55}")
    print(f"  Press  Q  in the window to quit")
    print(f"{'─'*55}\n")

    model = YOLO(model_path)
    cap   = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌  Cannot open video: {video_path}")
        return

    frame_idx    = 0
    last_results = None

    while True:
        ret, frame = cap.read()
        if not ret:
            # loop back to start
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
            if not ret:
                break

        # Run YOLO every YOLO_EVERY frames
        if frame_idx % YOLO_EVERY == 0:
            last_results = model(frame, conf=CONFIDENCE, verbose=False)[0]

        if last_results is not None:
            frame, count = draw_detections(frame, last_results)
            if frame_idx % 30 == 0:
                print(f"\r  Frame {frame_idx:5d}  |  Vehicles: {count}   ", end="", flush=True)

        cv2.imshow(WINDOW_TITLE, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("\n\n✅  Quit by user.")
            break

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()
    print("\nDemo finished.\n")


if __name__ == "__main__":
    main()
