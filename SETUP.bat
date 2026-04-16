@echo off
echo.
echo ===================================
echo Smart Parking System - Startup
echo ===================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/5] Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    pause
    exit /b 1
)

echo [2/5] Backend dependencies installed successfully!
cd ..

echo [3/5] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    pause
    exit /b 1
)

echo [4/5] Frontend dependencies installed successfully!
echo.
echo ===================================
echo Setup Complete!
echo ===================================
echo.
echo To start the application:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   npm run dev
echo.
echo Frontend will be available at: http://localhost:3000
echo Backend API docs at: http://localhost:8000/docs
echo.
pause
