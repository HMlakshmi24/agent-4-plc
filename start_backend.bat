@echo off
echo === Agent4PLC Backend Starter ===

:: Force UTF-8 so Python won't crash on emoji/unicode in print statements
set PYTHONUTF8=1
chcp 65001 >nul

:: Kill any existing process on port 8001
echo Checking port 8001...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8001 " ^| findstr "LISTENING\|ESTABLISHED\|CLOSE_WAIT"') do (
    echo Killing PID %%a on port 8001...
    taskkill /F /PID %%a 2>nul
)
timeout /t 2 /nobreak >nul

:: Activate the Python 3.10 venv and start backend
echo Starting backend on http://localhost:8001 ...
call "%~dp0venv310\Scripts\activate"
python "%~dp0backend\main.py"
pause
