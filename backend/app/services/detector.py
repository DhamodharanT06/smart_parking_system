import cv2
import json
import os
import threading
from ultralytics import YOLO
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from collections import Counter

# Vehicle classes to detect
VEHICLE_CLASSES = {'car', 'truck', 'bus', 'motorcycle', 'bicycle'}

# Slot coverage thresholds for partial vs full occupancy
# Coverage = intersection(slot, vehicle) / slot_area
FULL_OCCUPANCY_COVERAGE = 0.55
PARTIAL_OCCUPANCY_COVERAGE = 0.12


class ParkingDetector:
    """YOLO-based parking slot detector"""
    
    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.2):
        """Initialize detector with YOLO model"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model = YOLO(model_path)
        self.confidence = confidence
        self.last_detection = None
        self.detection_history = []
        self.detection_lock = threading.Lock()  # Thread-safe detection
        self.temporal_filter_size = 5  # 5-frame mode smoothing
    
    def detect_slots(self, frame, slots: List[Dict]) -> Dict:
        """
        Detect occupancy status for parking slots - thread-safe
        Supports free / partial / occupied states with temporal filtering.
        """
        if frame is None or len(slots) == 0:
            return {"slots": [], "timestamp": datetime.now().isoformat()}
        
        try:
            with self.detection_lock:
                results = self.model(frame, conf=self.confidence, verbose=False)
            
            detections = results[0]
            
            detected_vehicles = []
            if detections.boxes is not None:
                names = detections.names if hasattr(detections, 'names') else {}
                for box in detections.boxes:
                    cls_id = int(box.cls[0])
                    label = names.get(cls_id, str(cls_id))
                    if label.lower() not in VEHICLE_CLASSES:
                        continue
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    detected_vehicles.append({
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "confidence": float(box.conf[0]),
                        "label": label
                    })
            
            # Normalize and auto-align slots to current frame geometry.
            normalized_slots = self._prepare_slots(slots, frame.shape)

            # Analyze slots with one-vehicle-to-one-slot assignment.
            # This avoids a single large detection falsely occupying many slots.
            slot_status = self._classify_slots_with_assignment(normalized_slots, detected_vehicles)
            
            # Apply temporal filtering (5-frame mode smoothing)
            slot_status = self._apply_temporal_filter(slot_status)
            
            result = {
                "slots": slot_status,
                "timestamp": datetime.now().isoformat(),
                "vehicle_count": len(detected_vehicles)
            }
            
            with self.detection_lock:
                self.last_detection = result
                self.detection_history.append(result)
                if len(self.detection_history) > 100:
                    self.detection_history = self.detection_history[-100:]
            
            return result
        except Exception as e:
            print(f"Error in detect_slots: {e}")
            return {"slots": [], "timestamp": datetime.now().isoformat(), "error": str(e)}

    def _classify_slots_with_assignment(self, slots: List[Dict], vehicles: List[Dict]) -> List[Dict]:
        """Assign each vehicle to its best slot, then derive slot status from assigned coverage."""
        if not slots:
            return []

        assigned_coverage = [0.0 for _ in slots]

        for vehicle in vehicles:
            best_idx = -1
            best_score = 0.0
            best_cov = 0.0

            for idx, slot in enumerate(slots):
                coverage = self._calc_slot_coverage(slot, vehicle)
                center_hit = self._is_vehicle_center_in_slot(slot, vehicle)

                # Ignore weak overlaps that are unlikely to belong to this slot.
                if not center_hit and coverage < PARTIAL_OCCUPANCY_COVERAGE:
                    continue

                score = coverage + (0.5 if center_hit else 0.0)
                if score > best_score:
                    best_score = score
                    best_idx = idx
                    best_cov = max(coverage, PARTIAL_OCCUPANCY_COVERAGE if center_hit else 0.0)

            if best_idx >= 0:
                assigned_coverage[best_idx] = max(assigned_coverage[best_idx], best_cov)

        slot_status = []
        for idx, slot in enumerate(slots):
            overlap_val = assigned_coverage[idx]
            if overlap_val >= FULL_OCCUPANCY_COVERAGE:
                status = "occupied"
            elif overlap_val >= PARTIAL_OCCUPANCY_COVERAGE:
                status = "partial"
            else:
                status = "free"

            slot_status.append({
                "id": slot.get("id", idx),
                "x": slot["x"],
                "y": slot["y"],
                "width": slot["width"],
                "height": slot["height"],
                "status": status,
                "confidence": round(overlap_val, 2),
            })

        return slot_status

    def _prepare_slots(self, slots: List[Dict], frame_shape) -> List[Dict]:
        """Normalize slots and auto-scale coordinates when they don't match frame size."""
        normalized = [self._normalize_slot(slot, i) for i, slot in enumerate(slots)]
        return self._autoscale_slots_to_frame(normalized, frame_shape)

    def _autoscale_slots_to_frame(self, slots: List[Dict], frame_shape) -> List[Dict]:
        """Heuristic scaling for slot coordinates from a different reference resolution."""
        if not slots or frame_shape is None:
            return slots

        frame_h, frame_w = frame_shape[:2]
        max_x2 = max((s["x"] + s["width"] for s in slots), default=0)
        max_y2 = max((s["y"] + s["height"] for s in slots), default=0)
        if max_x2 <= 0 or max_y2 <= 0:
            return slots

        too_small = (max_x2 < frame_w * 0.80) and (max_y2 < frame_h * 0.80)
        too_large = (max_x2 > frame_w * 1.20) or (max_y2 > frame_h * 1.20)
        if not (too_small or too_large):
            return slots

        sx = frame_w / float(max_x2)
        sy = frame_h / float(max_y2)
        if not (0.5 <= sx <= 3.0 and 0.5 <= sy <= 3.0):
            return slots

        scaled = []
        for s in slots:
            scaled.append({
                "id": s.get("id"),
                "x": int(round(s["x"] * sx)),
                "y": int(round(s["y"] * sy)),
                "width": int(round(s["width"] * sx)),
                "height": int(round(s["height"] * sy)),
            })
        return scaled
    
    def _normalize_slot(self, slot: Dict, idx: int = 0) -> Dict:
        """Convert slot format x1,y1,x2,y2 to x,y,width,height"""
        if "x" in slot and "y" in slot and "width" in slot and "height" in slot:
            return slot
        elif "x1" in slot and "y1" in slot and "x2" in slot and "y2" in slot:
            return {
                "id": slot.get("id", idx),
                "x": slot["x1"],
                "y": slot["y1"],
                "width": slot["x2"] - slot["x1"],
                "height": slot["y2"] - slot["y1"]
            }
        else:
            return {
                "id": slot.get("id", idx),
                "x": slot.get("x", 0),
                "y": slot.get("y", 0),
                "width": slot.get("width", 50),
                "height": slot.get("height", 50)
            }

    @staticmethod
    def _calc_slot_coverage(slot: Dict, vehicle: Dict) -> float:
        """Calculate slot coverage by vehicle: intersection_area / slot_area."""
        sx1 = slot["x"]
        sy1 = slot["y"]
        sx2 = slot["x"] + slot["width"]
        sy2 = slot["y"] + slot["height"]

        vx1, vy1, vx2, vy2 = vehicle["x1"], vehicle["y1"], vehicle["x2"], vehicle["y2"]

        ix1 = max(sx1, vx1)
        iy1 = max(sy1, vy1)
        ix2 = min(sx2, vx2)
        iy2 = min(sy2, vy2)

        inter_w = max(0, ix2 - ix1)
        inter_h = max(0, iy2 - iy1)
        inter = inter_w * inter_h
        if inter <= 0:
            return 0.0

        slot_area = slot["width"] * slot["height"]
        if slot_area <= 0:
            return 0.0
        return inter / slot_area

    @staticmethod
    def _is_vehicle_center_in_slot(slot: Dict, vehicle: Dict) -> bool:
        """Check if detected vehicle center point lies inside the slot rectangle."""
        cx = (vehicle["x1"] + vehicle["x2"]) / 2.0
        cy = (vehicle["y1"] + vehicle["y2"]) / 2.0
        sx1 = slot["x"]
        sy1 = slot["y"]
        sx2 = slot["x"] + slot["width"]
        sy2 = slot["y"] + slot["height"]
        return sx1 <= cx <= sx2 and sy1 <= cy <= sy2

    def _get_slot_status(self, slot: Dict, vehicles: List[Dict]) -> Tuple[str, float]:
        """Return (status, max_coverage) for a single slot against all detected vehicles."""
        max_coverage = 0.0
        for v in vehicles:
            coverage = self._calc_slot_coverage(slot, v)

            # Center-hit protection catches partial overlaps where bbox is large.
            if self._is_vehicle_center_in_slot(slot, v):
                coverage = max(coverage, PARTIAL_OCCUPANCY_COVERAGE)

            if coverage > max_coverage:
                max_coverage = coverage

        if max_coverage >= FULL_OCCUPANCY_COVERAGE:
            return "occupied", max_coverage
        elif max_coverage >= PARTIAL_OCCUPANCY_COVERAGE:
            return "partial", max_coverage
        else:
            return "free", max_coverage

    def _is_slot_occupied(self, slot: Dict, vehicles: List[Dict]) -> bool:
        """Legacy helper — kept for backward compatibility"""
        status, _ = self._get_slot_status(slot, vehicles)
        return status in ("occupied", "partial")
    
    def _apply_temporal_filter(self, slot_status: List[Dict]) -> List[Dict]:
        """Apply 5-frame mode smoothing to reduce false detections (per paper)"""
        if len(self.detection_history) < self.temporal_filter_size:
            return slot_status
        
        filtered_status = []
        recent_history = self.detection_history[-self.temporal_filter_size:]
        
        for slot_idx, current_slot in enumerate(slot_status):
            # Collect status history for this slot
            status_history = []
            for detection in recent_history:
                if slot_idx < len(detection["slots"]):
                    status_history.append(detection["slots"][slot_idx]["status"])
            
            # Apply mode (most common value)
            if status_history:
                # Add current status
                status_history.append(current_slot["status"])
                
                mode_status = Counter(status_history).most_common(1)[0][0]
                current_slot["status"] = mode_status
            
            filtered_status.append(current_slot)
        
        return filtered_status


# ====================================================================== #
#  Slot Statistics                                                        #
# ====================================================================== #

class SlotAnalyzer:
    """Analyze parking slot statistics"""

    @staticmethod
    def calculate_statistics(slots: List[Dict]) -> Dict:
        total    = len(slots)
        occupied = sum(1 for s in slots if s["status"] == "occupied")
        partial  = sum(1 for s in slots if s["status"] == "partial")
        available = sum(1 for s in slots if s["status"] == "free")

        return {
            "total_slots":     total,
            "occupied_slots":  occupied,
            "partial_slots":   partial,
            "available_slots": available,
            "occupancy_rate":  ((occupied + partial) / total * 100) if total > 0 else 0,
        }
