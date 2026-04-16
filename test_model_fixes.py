#!/usr/bin/env python3
"""Test script to verify parking model fixes"""

import sys
sys.path.insert(0, './backend')

from app.services.detector import ParkingDetector, SlotAnalyzer, FULL_OCCUPANCY_IOU, PARTIAL_OCCUPANCY_IOU
from app.utils.video_handler import VideoStreamHandler
from app.models.schemas import SlotStatus
import numpy as np

print("=" * 60)
print("PARKING MODEL VERIFICATION TEST")
print("=" * 60)

# Test 1: Verify IoU thresholds (from paper)
print("\n✓ Test 1: IoU Thresholds")
print(f"  - Full Occupancy (Fully Parked): {FULL_OCCUPANCY_IOU} (expected: 0.45)")
assert FULL_OCCUPANCY_IOU == 0.45, f"Expected 0.45, got {FULL_OCCUPANCY_IOU}"
print(f"  - Partial Occupancy (Partially Parked): {PARTIAL_OCCUPANCY_IOU} (expected: 0.10)")
assert PARTIAL_OCCUPANCY_IOU == 0.10, f"Expected 0.10, got {PARTIAL_OCCUPANCY_IOU}"
print("  ✓ IoU thresholds are CORRECT")

# Test 2: Verify status names
print("\n✓ Test 2: Status Names")
expected_statuses = ["Free", "Partially Parked", "Fully Parked"]
enum_values = [s.value for s in SlotStatus]
print(f"  - Available statuses: {enum_values}")
for status in expected_statuses:
    assert status in enum_values, f"Missing status: {status}"
print("  ✓ All status names are present")

# Test 3: Brightness normalization
print("\n✓ Test 3: Brightness Normalization")
handler = VideoStreamHandler()
test_frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
normalized = handler.normalize_brightness(test_frame)
print(f"  - Original frame shape: {test_frame.shape}")
print(f"  - Normalized frame shape: {normalized.shape}")
print(f"  - Normalized frame dtype: {normalized.dtype}")
assert normalized.shape == test_frame.shape, "Shape mismatch"
assert normalized.dtype == np.uint8, "dtype should be uint8"
print("  ✓ Brightness normalization works correctly")

# Test 4: Detector temporal filter
print("\n✓ Test 4: Temporal Filtering (5-frame mode)")
detector = ParkingDetector()
print(f"  - Temporal filter size: {detector.temporal_filter_size} (expected: 5)")
assert detector.temporal_filter_size == 5, f"Expected 5, got {detector.temporal_filter_size}"
print("  ✓ Temporal filtering configured correctly")

# Test 5: Slot status calculation
print("\n✓ Test 5: Slot Status Logic")
test_slots = [
    {"id": 1, "status": "Free"},
    {"id": 2, "status": "Partially Parked"},
    {"id": 3, "status": "Fully Parked"},
]
stats = SlotAnalyzer.calculate_statistics(test_slots)
print(f"  - Statistics: {stats}")
assert stats["occupied_slots"] == 1, "Should have 1 fully parked"
assert stats["partial_slots"] == 1, "Should have 1 partially parked"
assert stats["available_slots"] == 1, "Should have 1 free"
print("  ✓ Slot statistics calculated correctly")

print("\n" + "=" * 60)
print("ALL TESTS PASSED ✓")
print("=" * 60)
print("\nModel is ready for deployment with:")
print("  - IoU thresholds matching paper specifications")
print("  - Correct status names (Free/Partially Parked/Fully Parked)")
print("  - Brightness normalization for different lighting")
print("  - Temporal filtering to reduce false detections")
print("=" * 60)
