#!/usr/bin/env python3
"""
Smart Parking System - Automatic Setup and Launch
Installs dependencies and starts both backend and frontend
"""

import subprocess
import sys
import os
import platform
import time
import webbrowser
from pathlib import Path

def is_command_available(cmd):
    """Check if a command is available in PATH"""
    return subprocess.run(
        f"where {cmd}" if platform.system() == "Windows" else f"which {cmd}",
        shell=True,
        capture_output=True
    ).returncode == 0

def run_command(cmd, cwd=None, description=""):
    """Run a shell command and handle errors"""
    print(f"\n{'='*60}")
    if description:
        print(f"📌 {description}")
    print(f"{'='*60}")
    print(f"Running: {cmd}\n")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=False
        )
        return result.returncode == 0
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def start_backend():
    """Start the backend server in a new terminal"""
    project_root = Path(__file__).parent
    backend_path = project_root / "backend"
    
    cmd = "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    
    if platform.system() == "Windows":
        subprocess.Popen(
            f'cmd /k cd /d "{backend_path}" && {cmd}',
            cwd=str(backend_path)
        )
    else:
        subprocess.Popen(
            f'gnome-terminal -- bash -c "cd {backend_path} && {cmd} ; bash"',
            shell=True
        )
    
    print("✓ Backend starting in new terminal...")
    time.sleep(3)

def start_frontend():
    """Start the frontend development server in a new terminal"""
    project_root = Path(__file__).parent
    frontend_path = project_root / "frontend"
    
    cmd = "npm run dev"
    
    if platform.system() == "Windows":
        subprocess.Popen(
            f'cmd /k cd /d "{frontend_path}" && {cmd}',
            cwd=str(frontend_path)
        )
    else:
        subprocess.Popen(
            f'gnome-terminal -- bash -c "cd {frontend_path} && {cmd} ; bash"',
            shell=True
        )
    
    print("✓ Frontend starting in new terminal...")
    time.sleep(3)

def main():
    print("\n" + "="*60)
    print("🚗  SMART PARKING SYSTEM - AUTOMATIC SETUP")
    print("="*60)
    
    # Check prerequisites
    print("\n🔍 Checking prerequisites...")
    
    if not is_command_available("python"):
        print("❌ Python is not installed or not in PATH")
        print("   Download from: https://www.python.org/downloads/")
        sys.exit(1)
    print("✓ Python found")
    
    if not is_command_available("node"):
        print("❌ Node.js is not installed or not in PATH")
        print("   Download from: https://nodejs.org/")
        sys.exit(1)
    print("✓ Node.js found")
    
    # Setup backend
    project_root = Path(__file__).parent
    backend_path = project_root / "backend"
    frontend_path = project_root / "frontend"
    
    print("\n📦 Setting up backend...")
    if not run_command(
        "pip install -r requirements.txt",
        cwd=str(backend_path),
        description="Installing Python packages"
    ):
        print("⚠ Some packages failed to install, but continuing...")
    
    print("\n📦 Setting up frontend...")
    if not run_command(
        "npm install",
        cwd=str(frontend_path),
        description="Installing Node packages"
    ):
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Run health check
    print("\n🏥 Running health check...")
    os.chdir(str(backend_path))
    result = subprocess.run(
        "python check_system.py",
        shell=True,
        capture_output=False
    )
    
    if result.returncode != 0:
        print("\n⚠ Health check found issues, but trying to continue...")
    
    # Start services
    print("\n\n" + "="*60)
    print("🚀 STARTING SERVICES")
    print("="*60)
    
    print("\n🔄 Starting backend...")
    start_backend()
    
    print("\n🔄 Starting frontend...")
    start_frontend()
    
    # Wait for services to start
    print("\n⏳ Waiting for services to start...")
    time.sleep(8)
    
    # Open browser
    print("\n✓ Services started!")
    print("\nOpening http://localhost:3000 in your browser...")
    
    webbrowser.open("http://localhost:3000")
    
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("\n📱 Frontend: http://localhost:3000")
    print("🔌 Backend API: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\n💡 Close this window when done, or press Ctrl+C")
    print("\nNote: Backend and Frontend are running in separate terminals\n")
    
    # Keep this window open
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
