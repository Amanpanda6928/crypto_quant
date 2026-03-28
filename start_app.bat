@echo off
title Crypto Quant Trading System
echo.
echo ========================================
echo    Crypto Quant Trading System
echo ========================================
echo.
echo Backend: http://127.0.0.1:8000
echo Frontend: http://localhost:3000
echo API Docs: http://127.0.0.1:8000/docs
echo.
echo Login: Any username/password
echo ========================================
echo.

REM Check if Node.js is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ Node.js/npm not found!
    echo 📥 Please install from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo ✅ Node.js found
echo.

REM Start backend in new window
start "Backend Server" cmd /k "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

REM Wait a moment then start frontend
timeout /t 3 /nobreak >nul
start "Frontend Server" cmd /k "cd /d %~dp0frontend && npm start"

echo.
echo 🚀 Services started! Check the new windows.
echo 🌐 Open: http://localhost:3000
echo.
pause
