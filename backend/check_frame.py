"""Quick check: generate a test frame using exactly main.py draw logic, compare sizes."""
import cv2, json, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COLORS = [
    (56,56,255),(151,157,255),(31,112,255),(29,178,255),(49,210,207),(10,249,72),
    (23,204,146),(134,219,61),(52,147,26),(187,212,0),(168,153,44),(255,194,0),
    (147,69,52),(255,113,0),(0,121,255),(255,49,197),
]
VEHICLE_CLASSES = {'car','truck','bus','motorcycle','bicycle'}

from ultralytics import YOLO
model = YOLO('yolov8n.pt')

cap = cv2.VideoCapture('backend/parking_test_video.mp4')
ret, frame = cap.read()
cap.release()
if not ret:
    print('ERROR: cannot read frame')
    exit(1)

print(f'Frame shape: {frame.shape}')

results = model(frame, conf=0.2, verbose=False)[0]
names = results.names
count = 0

for box in results.boxes:
    cls_id = int(box.cls[0])
    label = names.get(cls_id, '')
    if label.lower() not in VEHICLE_CLASSES:
        continue
    count += 1
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    conf = float(box.conf[0])
    color = COLORS[cls_id % len(COLORS)]
    txt = f'{label} {conf:.2f}'
    (tw, th), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, txt, (x1+2, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

banner = f'Vehicles Detected: {count}'
(bw, bh), _ = cv2.getTextSize(banner, cv2.FONT_HERSHEY_SIMPLEX, 0.75, 2)
cv2.rectangle(frame, (0, 0), (bw+20, bh+18), (0, 0, 0), -1)
cv2.putText(frame, banner, (10, bh+8), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 230, 80), 2)

out = 'backend/debug_frames/debug_frame_check.jpg'
cv2.imwrite(out, frame)
print(f'Saved {out} | vehicles={count}')

# Compare with existing debug frames
for name in ['debug_frame_root.jpg', 'backend/debug_frames/debug_frame_camera_0.jpg']:
    if os.path.exists(name):
        img = cv2.imread(name)
        print(f'{name}: {img.shape if img is not None else "unreadable"}')
