#!/bin/bash

echo "========================================"
echo " GemVision Backend Startup Script"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "Checking dependencies..."
pip install -r backend/requirements.txt --quiet

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file not found!"
    echo "Please copy .env.example to .env and add your API keys."
    echo ""
    exit 1
fi

# Initialize database
echo "Initializing database..."
python -m backend.models.database

# Start backend server
echo ""
echo "========================================"
echo " Starting FastAPI Backend Server"
echo " Access at: http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo "========================================"
echo ""
python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
