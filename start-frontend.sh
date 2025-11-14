#!/bin/bash

echo "========================================"
echo " GemVision Frontend Startup Script"
echo "========================================"
echo ""

cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Check if .env.local exists
if [ ! -f ".env.local" ]; then
    echo ""
    echo "WARNING: .env.local file not found!"
    echo "Creating from example..."
    cp .env.local.example .env.local
    echo ""
    echo "Please update .env.local with your configuration."
    echo ""
fi

# Start development server
echo ""
echo "========================================"
echo " Starting Next.js Development Server"
echo " Access at: http://localhost:3000"
echo "========================================"
echo ""
npm run dev
