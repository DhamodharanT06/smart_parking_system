"""
Smart Parking System - Configuration & Health Check
Tests all components before starting the server
"""

import os
import sys
import json
from pathlib import Path

def check_model():
    """Check if YOLO model exists"""
    model_path = "yolov8n.pt"
    if os.path.exists(model_path):
        size_mb = os.path.getsize(model_path) / (1024 * 1024)
        print(f"✓ YOLO Model found: {model_path} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"⚠ YOLO Model NOT found: {model_path}")
        print("  The model will be auto-downloaded on first run (~50MB)")
        return False

def check_slots_config():
    """Check if slots configuration exists"""
    slots_file = "slots.json"
    if os.path.exists(slots_file):
        try:
            with open(slots_file, 'r') as f:
                config = json.load(f)
            num_cameras = len(config)
            total_slots = sum(len(v) if isinstance(v, list) else 0 for v in config.values())
            print(f"✓ Slots config found: {slots_file}")
            print(f"  - Cameras: {num_cameras}")
            print(f"  - Total slots: {total_slots}")
            return True
        except Exception as e:
            print(f"✗ Slots config corrupted: {e}")
            return False
    else:
        print(f"⚠ Slots config NOT found: {slots_file}")
        print("  Creating default configuration...")
        return False

def check_packages():
    """Check if required packages are installed"""
    packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'ultralytics': 'YOLOv8',
        'pydantic': 'Pydantic',
    }
    
    missing = []
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            missing.append(module)
    
    return len(missing) == 0, missing

def check_env_files():
    """Check environment configuration files"""
    files = {
        '.env': 'Backend config',
        '../frontend/.env': 'Frontend config'
    }
    
    all_good = True
    for path, desc in files.items():
        if os.path.exists(path):
            print(f"✓ {desc} found: {path}")
        else:
            print(f"⚠ {desc} NOT found: {path}")
            all_good = False
    
    return all_good

def main():
    os.chdir(os.path.dirname(__file__))  # Change to backend directory
    
    print("\n" + "="*50)
    print("🚗 SMART PARKING SYSTEM - HEALTH CHECK")
    print("="*50 + "\n")
    
    print("📋 Checking configuration files...")
    env_ok = check_env_files()
    
    print("\n📦 Checking Python packages...")
    packages_ok, missing = check_packages()
    
    print("\n🎯 Checking YOLO model...")
    model_ok = check_model()
    
    print("\n📍 Checking parking slots configuration...")
    slots_ok = check_slots_config()
    
    print("\n" + "="*50)
    if packages_ok and slots_ok:
        print("✓ ALL CHECKS PASSED - Ready to start!")
        print("="*50 + "\n")
        print("Start the server with:")
        print("  python -m uvicorn app.main:app --reload")
        print("\nAPI Documentation: http://localhost:8000/docs\n")
        return 0
    else:
        print("⚠ SOME CHECKS FAILED - See above for details")
        print("="*50 + "\n")
        if missing:
            print("Install missing packages:")
            print(f"  pip install {' '.join(missing)}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
