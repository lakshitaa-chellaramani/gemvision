@echo off
echo ========================================
echo  GemVision Frontend Startup Script
echo ========================================
echo.

cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Check if .env.local exists
if not exist ".env.local" (
    echo.
    echo WARNING: .env.local file not found!
    echo Creating from example...
    copy .env.local.example .env.local
    echo.
    echo Please update .env.local with your configuration.
    echo.
)

REM Start development server
echo.
echo ========================================
echo  Starting Next.js Development Server
echo  Access at: http://localhost:3000
echo ========================================
echo.
call npm run dev

pause
