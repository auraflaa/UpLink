@echo off
echo ===================================================
echo UpLink - Development Server
echo ===================================================
echo.

echo [1/2] Installing dependencies...
call npm install

echo.
echo [2/2] Starting the development server...
echo The application will be available at http://localhost:3000
echo.
call npm run dev

pause
