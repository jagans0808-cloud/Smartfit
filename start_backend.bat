@echo off
title SmartFit - FastAPI Backend API Server
echo ========================================================
echo Starting SmartFit Backend API (Port 8000)
echo WebSocket Live Feed: ws://127.0.0.1:8000/ws/live
echo REST API Docs: http://127.0.0.1:8000/docs
echo ========================================================
cd /d %~dp0backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
