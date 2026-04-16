import json
import math
import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

import cv2

from app.services.detector import VEHICLE_CLASSES


class SlotCalibrator:
    """Calibrate parking slot coordinates from multiple sampled frames."""

    @staticmethod
    def _extract_vehicle_boxes(detector, frame) -> List[Dict]:
        with detector.detection_lock:
            results = detector.model(frame, conf=detector.confidence, verbose=False)
        det = results[0]

        boxes = []
        names = det.names if hasattr(det, "names") else {}
        if det.boxes is None:
            return boxes

        for box in det.boxes:
            cls_id = int(box.cls[0])
            label = names.get(cls_id, str(cls_id))
            if label.lower() not in VEHICLE_CLASSES:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            boxes.append(
                {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    "confidence": float(box.conf[0]),
                    "label": label,
                }
            )

        return boxes

    @staticmethod
    def _iou(a: Dict, b: Dict) -> float:
        ix1 = max(a["x1"], b["x1"])
        iy1 = max(a["y1"], b["y1"])
        ix2 = min(a["x2"], b["x2"])
        iy2 = min(a["y2"], b["y2"])

        inter_w = max(0, ix2 - ix1)
        inter_h = max(0, iy2 - iy1)
        inter = inter_w * inter_h
        if inter <= 0:
            return 0.0

        a_area = max(1, (a["x2"] - a["x1"]) * (a["y2"] - a["y1"]))
        b_area = max(1, (b["x2"] - b["x1"]) * (b["y2"] - b["y1"]))
        union = a_area + b_area - inter
        return inter / union if union > 0 else 0.0

    @staticmethod
    def _center(box: Dict) -> tuple:
        return ((box["x1"] + box["x2"]) / 2.0, (box["y1"] + box["y2"]) / 2.0)

    @classmethod
    def _cluster_boxes(cls, samples: List[Dict], min_support: int = 2) -> List[Dict]:
        clusters: List[Dict] = []

        for item in samples:
            box = item["box"]
            frame_idx = item["frame_idx"]

            best_idx = -1
            best_score = -1.0

            for i, c in enumerate(clusters):
                iou = cls._iou(box, c)
                cx1, cy1 = cls._center(box)
                cx2, cy2 = cls._center(c)
                dist = math.hypot(cx1 - cx2, cy1 - cy2)
                c_w = max(1.0, c["x2"] - c["x1"])
                c_h = max(1.0, c["y2"] - c["y1"])
                dist_norm = dist / max(c_w, c_h)

                score = iou - 0.25 * dist_norm
                if (iou >= 0.30 or dist_norm <= 0.55) and score > best_score:
                    best_score = score
                    best_idx = i

            if best_idx == -1:
                new_cluster = {
                    "x1": box["x1"],
                    "y1": box["y1"],
                    "x2": box["x2"],
                    "y2": box["y2"],
                    "hits": 1,
                    "frames": {frame_idx},
                }
                clusters.append(new_cluster)
            else:
                c = clusters[best_idx]
                n = c["hits"]
                c["x1"] = (c["x1"] * n + box["x1"]) / (n + 1)
                c["y1"] = (c["y1"] * n + box["y1"]) / (n + 1)
                c["x2"] = (c["x2"] * n + box["x2"]) / (n + 1)
                c["y2"] = (c["y2"] * n + box["y2"]) / (n + 1)
                c["hits"] = n + 1
                c["frames"].add(frame_idx)

        supported = [c for c in clusters if len(c["frames"]) >= min_support]
        if not supported:
            supported = [c for c in clusters if c["hits"] >= max(1, min_support)]

        supported.sort(key=lambda c: (len(c["frames"]), c["hits"]), reverse=True)
        return supported

    @staticmethod
    def _cluster_to_slot(cluster: Dict, frame_w: int, frame_h: int) -> Dict:
        # Expand slightly to cover the parked vehicle footprint.
        pad_x = int(max(6, (cluster["x2"] - cluster["x1"]) * 0.08))
        pad_y = int(max(6, (cluster["y2"] - cluster["y1"]) * 0.08))

        x1 = max(0, int(round(cluster["x1"])) - pad_x)
        y1 = max(0, int(round(cluster["y1"])) - pad_y)
        x2 = min(frame_w - 1, int(round(cluster["x2"])) + pad_x)
        y2 = min(frame_h - 1, int(round(cluster["y2"])) + pad_y)

        return {
            "x": x1,
            "y": y1,
            "width": max(1, x2 - x1),
            "height": max(1, y2 - y1),
        }

    @classmethod
    def calibrate_from_camera(
        cls,
        camera_manager,
        detector,
        stream_handler,
        camera_id: str,
        sample_frames: int = 8,
        min_support_frames: int = 2,
        target_slots: Optional[int] = None,
    ) -> Dict:
        camera = camera_manager.get_camera(camera_id)
        if not camera:
            raise ValueError(f"Camera '{camera_id}' not found")

        cap = camera_manager.open_camera_source(camera_id)
        if not cap or not cap.isOpened():
            raise RuntimeError("Unable to open camera source for calibration")

        backend_dir = Path(__file__).resolve().parents[2]
        temp_dir = backend_dir / "debug_frames" / f"calibration_temp_{camera_id}"
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        temp_dir.mkdir(parents=True, exist_ok=True)

        sampled = 0
        samples: List[Dict] = []
        base_frame: Optional[any] = None
        frame_h = 0
        frame_w = 0

        try:
            for i in range(sample_frames):
                # For file/live streams: skip some frames between samples.
                for _ in range(8):
                    cap.read()

                ret, frame = cap.read()
                if not ret or frame is None:
                    continue

                frame = stream_handler.normalize_brightness(frame)
                frame_h, frame_w = frame.shape[:2]

                if base_frame is None:
                    base_frame = frame.copy()

                boxes = cls._extract_vehicle_boxes(detector, frame)
                vis = frame.copy()
                for b in boxes:
                    cv2.rectangle(vis, (b["x1"], b["y1"]), (b["x2"], b["y2"]), (0, 200, 255), 2)

                cv2.imwrite(str(temp_dir / f"sample_{i + 1}.jpg"), vis)

                for b in boxes:
                    samples.append({"frame_idx": i, "box": b})

                sampled += 1

            if sampled < 2:
                raise RuntimeError("Calibration needs at least 2 readable frames")

            if not samples:
                raise RuntimeError("No vehicles detected in sampled frames for calibration")

            clusters = cls._cluster_boxes(samples, min_support=min_support_frames)
            if not clusters:
                raise RuntimeError("Could not infer stable parking slots from sampled frames")

            slots = []
            for c in clusters:
                slot = cls._cluster_to_slot(c, frame_w, frame_h)
                slot["support"] = len(c["frames"])
                slots.append(slot)

            # Remove near-duplicates by IoU.
            deduped: List[Dict] = []
            for s in slots:
                box_s = {"x1": s["x"], "y1": s["y"], "x2": s["x"] + s["width"], "y2": s["y"] + s["height"]}
                duplicate = False
                for d in deduped:
                    box_d = {"x1": d["x"], "y1": d["y"], "x2": d["x"] + d["width"], "y2": d["y"] + d["height"]}
                    if cls._iou(box_s, box_d) > 0.65:
                        duplicate = True
                        break
                if not duplicate:
                    deduped.append(s)

            expected_slots = int(target_slots or 0)
            if expected_slots <= 0:
                cam_slots = int(camera.get("total_slots") or 0)
                # Guard against bad auto-updated values.
                expected_slots = cam_slots if 0 < cam_slots <= 20 else 12
            if expected_slots > 0 and len(deduped) > expected_slots:
                deduped.sort(key=lambda s: s.get("support", 0), reverse=True)
                deduped = deduped[:expected_slots]

            deduped.sort(key=lambda s: (s["y"], s["x"]))
            final_slots = []
            for i, s in enumerate(deduped, start=1):
                final_slots.append(
                    {
                        "id": i,
                        "x": int(s["x"]),
                        "y": int(s["y"]),
                        "width": int(s["width"]),
                        "height": int(s["height"]),
                    }
                )

            if not final_slots:
                raise RuntimeError("Calibration produced 0 slots")

            # Persist slots in slots.json under source and basename keys.
            slots_path = camera_manager.slots_config_path
            config = {}
            if os.path.exists(slots_path):
                with open(slots_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        config = loaded

            source = camera.get("video_source", "")
            if source:
                config[source] = final_slots
                base = os.path.basename(source)
                if base:
                    config[base] = final_slots
                abs_source = os.path.abspath(source)
                config[abs_source] = final_slots

            with open(slots_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            camera_manager.set_camera_total_slots(camera_id, len(final_slots))

            # Save final debug output image.
            out = base_frame.copy() if base_frame is not None else frame.copy()
            for s in final_slots:
                x, y, w, h = s["x"], s["y"], s["width"], s["height"]
                cv2.rectangle(out, (x, y), (x + w, y + h), (0, 220, 60), 2)
                cv2.putText(out, f"#{s['id']}", (x + 2, max(12, y - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            debug_path = stream_handler.save_debug_frame(out, camera_id)

            return {
                "camera_id": camera_id,
                "sampled_frames": sampled,
                "used_frames_for_training": sampled,
                "slot_count": len(final_slots),
                "slots": final_slots,
                "debug_frame": debug_path,
                "slots_file": slots_path,
                "temp_cleared": True,
            }
        finally:
            camera_manager.close_camera_source(camera_id)
            shutil.rmtree(temp_dir, ignore_errors=True)
