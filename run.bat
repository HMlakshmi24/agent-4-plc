@echo off
REM Agent4PLC v2.0 - Quick Start Script for Windows

echo.
echo ========================================
echo   Agent4PLC v2.0 - Localhost Edition
echo ========================================
echo.

REM Check if running from correct directory
if not exist "backend" (
    echo ERROR: backend folder not found!
    echo Please run this script from the agent-4-plc root directory
    pause
    exit /b 1
)

REM Show menu
echo Select what to run:
echo.
echo 1. Start Backend Only (FastAPI on 127.0.0.1:8000)
echo 2. Start Frontend Only (React on localhost:5173)
echo 3. Start Both (Backend + Frontend)
echo.
set /p choice="Enter your choice (1-3): "

if "%choice%"=="1" goto start_backend
if "%choice%"=="2" goto start_frontend
if "%choice%"=="3" goto start_both
echo Invalid choice
pause
exit /b 1

:start_backend
echo.
echo Starting Backend (FastAPI)...
echo Endpoint: http://127.0.0.1:8000
echo Docs: http://127.0.0.1:8000/docs
echo.
cd backend
python main.py
cd ..
pause
exit /b 0

:start_frontend
echo.
echo Starting Frontend (React + Vite)...
echo URL: http://localhost:5173
echo.
cd frontend
npm run dev
cd ..
pause
exit /b 0

:start_both
echo.
echo Starting Agent4PLC v2.0...
echo.
echo Backend will run on: http://127.0.0.1:8000
echo Frontend will run on: http://localhost:5173
echo.
echo Waiting for you to start terminals...
echo This script will show instructions for starting both.
echo.
echo INSTRUCTIONS:
echo 1. Open TWO new terminal windows
echo 2. In first terminal, run:
echo    cd backend
echo    python main.py
echo.
echo 3. In second terminal, run:
echo    cd frontend
echo    npm run dev
echo.
echo 4. Open browser to http://localhost:5173
echo.
pause
exit /b 0
