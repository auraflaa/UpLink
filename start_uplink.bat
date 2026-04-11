@echo off
title UpLink - Full Stack Launcher
color 0B
echo.
echo ===================================================
echo               UpLink System Launcher               
echo ===================================================
echo.
echo [*] Starting Backend Cluster (Powershell)...
start "UpLink Backend Host" powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_backend.ps1"

echo [*] Starting Frontend Server (Node.js)...
start "UpLink Frontend Host" cmd /c "%~dp0Frontend\start.bat"

echo.
echo [OK] Both systems have been launched in separate windows!
echo Please wait a moment for the ports to bind.
echo   - Frontend: http://localhost:3000
echo   - Backend: http://127.0.0.1:8000
echo.
pause
