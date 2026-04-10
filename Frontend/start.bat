@echo off
title UpLink - Development Server
cd /d %~dp0
cls

echo ===================================================
echo    UpLink - Neural Intelligence Hub [V3]
echo ===================================================
echo.

if not exist "node_modules\" (
    echo [1/2] node_modules not detected. 
    echo Downloading neural dependencies...
    call npm install
) else (
    echo [1/2] Workspace verified.
)

echo.
echo [2/2] Starting the development server...
echo The application will be available at http://localhost:3000
echo.

call npm run dev -- --open

pause
