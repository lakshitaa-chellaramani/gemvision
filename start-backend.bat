@echo off
echo ========================================
echo  GemVision Backend Startup Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    cd ..
)

REM Activate virtual environment
echo Activating virtual environment...
call backend\venv\Scripts\activate

REM Install dependencies if needed
echo Checking dependencies...
pip install -r backend\requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and add your API keys.
    echo.
    pause
    exit /b 1
)

REM Initialize database
echo Initializing database...
python -m backend.models.database

REM Start backend server
echo.
echo ========================================
echo  Starting FastAPI Backend Server
echo  Access at: http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo ========================================
echo.
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

pause
