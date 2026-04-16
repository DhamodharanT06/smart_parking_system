import cv2
import json
import os
from pathlib import Path
from ultralytics import YOLO
import argparse

# CLI flags
parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--debug', action='store_true', help='Run a short debug pass and save a debug image')
parser.add_argument('--conf', type=float, default=0.2, help='Confidence threshold for detection')
parser.add_argument('--model', type=str, default='yolov8n.pt', help='YOLO model path')
parser.add_argument('--frames', type=int, default=5, help='Number of frames to run in debug mode')
parser.add_argument('--video', type=str, default=None, help='Alternate video file to run')
args, _ = parser.parse_known_args()

# --- VIDEO CONFIGURATION ---
VIDEO_FILE = "parking_test_video.mp4"  # Default video
DEFAULT_SLOT_FILE = 'slots.json'

def choose_capture_mode():
    """Prompt user to choose capture mode: video or camera. Returns a tuple
    (mode, source). mode is 'video' or 'camera'. source is path or camera index."""
    while True:
        try:
            choice = input("Select capture mode - video or camera? (v/c) [v]: ").strip().lower()
        except Exception:
            # If input() not available, fall back to args.video
            choice = 'v' if args.video else 'c'
        if choice == 'c' or choice == 'camera':
            try:
                idx = input("Enter camera index [0]: ").strip()
            except Exception:
                idx = ''
            idx = int(idx) if idx.isdigit() else 0
            return 'camera', idx
        # treat anything else as video (default)
        try:
            path = input(f"Enter video path [{args.video or VIDEO_FILE}]: ").strip()
        except Exception:
            path = args.video or VIDEO_FILE
        if path == '':
            path = args.video or VIDEO_FILE
        return 'video', path

def get_slots_for_video(video_path, slots_file='slots.json'):
    """
    Load slots from JSON file using video path as key.
    
    JSON Structure:
    {
      "camera1.mp4": [slot1, slot2, ...],
      "camera2.mp4": [slot1, slot2, ...],
    }
    
    Example:
        get_slots_for_video("camera1.mp4") → returns slots for camera1
    """
    if not os.path.exists(slots_file):
        print(f"✓ No slots file found: {slots_file}")
        return None
    
    try:
        with open(slots_file, 'r') as f:
            all_slots = json.load(f)
        
        # If it's a dict with video paths as keys
        if isinstance(all_slots, dict):
            if video_path in all_slots:
                print(f"✓ Loaded slots for video: {video_path}")
                return all_slots[video_path]
            else:
                print(f"⚠ No slots found for video: {video_path}")
                print(f"   Available videos: {list(all_slots.keys())}")
                return None
        
        # If it's a list (old format), return as-is
        elif isinstance(all_slots, list):
            print(f"✓ Loaded slots (legacy format)")
            return all_slots
        else:
            return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in {slots_file}")
        return None

def save_slots_for_video(video_path, slots, slots_file='slots.json'):
    """
    Save slots to JSON file using video path as key.
    Preserves existing slots for other videos.
    """
    # Load existing data
    all_slots = {}
    if os.path.exists(slots_file):
        try:
            with open(slots_file, 'r') as f:
                existing = json.load(f)
                if isinstance(existing, dict):
                    all_slots = existing
        except:
            pass
    
    # Add/update slots for this video
    all_slots[video_path] = slots
    
    # Save back
    with open(slots_file, 'w') as f:
        json.dump(all_slots, f, indent=2)
    print(f"✅ Saved {len(slots)} slots for video: {video_path}")

# --- IOU FUNCTION ---
def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    if interArea == 0:
        return 0.0
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return interArea / float(boxAArea + boxBArea - interArea)

# --- MANUAL SLOT DRAWING MODE ---
def setup_parking_slots(video_path, slots_file):
    print("⚙️ No valid slots found for this video — entering setup mode...")
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        print("❌ Could not access video.")
        return []

    slots, drawing, ix, iy = [], False, -1, -1

    def draw_rect(event, x, y, flags, param):
        nonlocal drawing, ix, iy
        temp = param.copy()
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            ix, iy = x, y
        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            cv2.rectangle(temp, (ix, iy), (x, y), (255, 0, 0), 2)
            cv2.imshow("Mark Parking Slots", temp)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            cv2.rectangle(param, (ix, iy), (x, y), (0, 255, 0), 2)
            slots.append({"x1": ix, "y1": iy, "x2": x, "y2": y})
            cv2.imshow("Mark Parking Slots", param)

    cv2.imshow("Mark Parking Slots", frame)
    cv2.setMouseCallback("Mark Parking Slots", draw_rect, frame)
    print("🖱️ Draw parking areas (Press 's' to save, 'q' to quit).")

    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            save_slots_for_video(video_path, slots, slots_file)
            break
        elif key == ord('q'):
            break
    cv2.destroyAllWindows()
    return slots

# --- LOAD OR SETUP SLOTS ---
# Ask user for capture mode (video or camera)
mode, source = choose_capture_mode()
slots = []
video_to_open = None
camera_index = None
if mode == 'video':
    video_to_open = source
    print(f"📍 Loading parking slots for: {video_to_open}")
    slots = get_slots_for_video(video_to_open, DEFAULT_SLOT_FILE)
    if slots is None or len(slots) == 0:
        print("⚠️  No slots found for this video. You can annotate now.")
        # offer annotation only if we can open the video
        try:
            temp_cap = cv2.VideoCapture(video_to_open)
            if temp_cap.isOpened():
                temp_cap.release()
                slots = setup_parking_slots(video_to_open, DEFAULT_SLOT_FILE)
            else:
                print(f"❌ Could not open video: {video_to_open}")
        except Exception:
            pass
    if not slots:
        slots = []
else:
    camera_index = int(source)
    print(f"📍 Camera mode selected (index={camera_index}). Slots will not be auto-loaded.")

# --- YOLO MODEL ---
model = YOLO(args.model)

# ── Color palette (BGR) — one distinct color per YOLO class id ──────────────
_COLORS = [
    (56, 56, 255), (151, 157, 255), (31, 112, 255), (29, 178, 255),
    (49, 210, 207), (10, 249, 72),  (23, 204, 146), (134, 219, 61),
    (52, 147,  26), (187, 212,  0), (168, 153,  44), (255, 194,  0),
    (147,  69,  52), (255, 113,  0), (0, 121, 255),  (255,  49, 197),
]

def draw_frame(frame, results):
    """Draw YOLO vehicle detections on frame — matches debug_frame_root.jpg style."""
    names   = results.names if hasattr(results, 'names') else {}
    boxes   = results.boxes if results.boxes is not None else []
    count   = 0
    vehicles = []

    for box in boxes:
        cls_id = int(box.cls[0])
        label  = names.get(cls_id, str(cls_id))
        if label.lower() not in VEHICLE_CLASSES:
            continue
        count += 1
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        conf  = float(box.conf[0])
        color = _COLORS[cls_id % len(_COLORS)]
        vehicles.append([x1, y1, x2, y2])

        # Filled label background
        txt = f"{label} {conf:.2f}"
        (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, txt, (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        # Bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

    # Top-left count banner
    banner = f"Vehicles Detected: {count}"
    (bw, bh), _ = cv2.getTextSize(banner, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
    cv2.rectangle(frame, (0, 0), (bw + 20, bh + 18), (0, 0, 0), -1)
    cv2.putText(frame, banner, (10, bh + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 230, 80), 2)

    return frame, count, vehicles


# --- CAMERA STREAM -----------------------------------------------------------
CONFIDENCE_THRESHOLD = args.conf
VEHICLE_CLASSES = {'car', 'truck', 'bus', 'motorcycle', 'bicycle'}
YOLO_EVERY = 3   # run YOLO every N frames (keeps display smooth)

if mode == 'video':
    vpath = video_to_open or args.video or VIDEO_FILE
    cap = cv2.VideoCapture(vpath)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video: {vpath}")
        exit(1)
    print(f"🎥 Starting detection from video: {vpath}")
else:
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"❌ Error: Could not open camera index: {camera_index}")
        exit(1)
    print(f"🎥 Starting detection from camera index: {camera_index}")

print(f"   Confidence threshold: {CONFIDENCE_THRESHOLD}")
print(f"   Vehicle classes: {VEHICLE_CLASSES}")
print("   Press 'q' to quit...\n")

frame_idx    = 0
last_results = None

while True:
    ret, frame = cap.read()
    if not ret:
        # Loop video back to start instead of stopping
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret:
            break

    # Run YOLO every YOLO_EVERY frames; reuse cached results in between
    if frame_idx % YOLO_EVERY == 0:
        last_results = model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)[0]

    annotated, count, vehicles = draw_frame(frame, last_results) if last_results else (frame, 0, [])

    # Print stats every ~30 frames
    if frame_idx % 30 == 0:
        print(f"\r  Frame {frame_idx:5d}  |  Vehicles: {count}   ", end="", flush=True)

    # Debug mode — save frame and exit after N frames
    if args.debug:
        cv2.imwrite('debug_frame_root.jpg', annotated)
        if 'frame_iter' not in globals():
            frame_iter = 1
        else:
            frame_iter += 1
        if frame_iter >= args.frames:
            print(f'\nDebug pass complete — saved debug_frame_root.jpg ({count} vehicles)')
            break

    cv2.imshow("Smart Parking System — Live Detection  |  Press Q to quit", annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("\n\n✅  Quit by user.")
        break

    frame_idx += 1

cap.release()
cv2.destroyAllWindows()
print("\nDone.\n")