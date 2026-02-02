@echo off
REM Agent4PLC Startup Script for Windows
REM This script starts both backend and frontend

echo.
echo ===============================================================================
echo   AGENT4PLC v2.0 STARTUP
echo ===============================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if Node.js/npm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js/npm is not installed or not in PATH
    echo Please install Node.js and add it to your PATH
    pause
    exit /b 1
)

echo [INFO] Python and Node.js found
echo.

REM Create two terminal windows for backend and frontend
echo [1/2] Starting BACKEND on http://127.0.0.1:8001
start "Agent4PLC Backend" cmd /k "cd backend && python main.py"

timeout /t 3 /nobreak
echo.
echo [2/2] Starting FRONTEND on http://localhost:5173
start "Agent4PLC Frontend" cmd /k "cd frontend && npm run dev || pause"

echo.
echo ===============================================================================
echo   STARTUP COMPLETE
echo ===============================================================================
echo.
echo Backend:  http://127.0.0.1:8001
echo Frontend: http://localhost:5173
echo.
echo Open http://localhost:5173 in your browser to use Agent4PLC
echo.
echo Press any key to exit this window (other windows will stay open)
pause
