@echo off
title SmartFit - Integrated Fitness Monitoring System
echo ========================================================
echo   SMARTFIT - INTEGRATED FITNESS MONITORING SYSTEM
echo   Biomedfinix2 - SIH26213 Multimodal Wearable Platform
echo ========================================================
echo.
echo Launching Backend Server (FastAPI + WebSocket)...
start "SmartFit Backend Server" cmd /k "cd /d %~dp0 && call start_backend.bat"

timeout /t 2 /nobreak >nul

echo Launching Frontend Dashboard (React + Vite)...
start "SmartFit Frontend Dashboard" cmd /k "cd /d %~dp0 && call start_frontend.bat"

echo.
echo ========================================================
echo System launched!
echo - Frontend: http://localhost:5173
echo - Backend API: http://127.0.0.1:8000/docs
echo - Live WebSocket: ws://127.0.0.1:8000/ws/live
echo ========================================================
