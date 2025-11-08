#!/bin/bash

echo "=========================================="
echo "Healthcare Authentication System Launcher"
echo "=========================================="
echo ""

# Check if required Python packages are installed
echo "Checking dependencies..."

if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "Error: FastAPI is not installed. Installing..."
    pip install fastapi uvicorn python-multipart
fi

if ! python3 -c "import flask" 2>/dev/null; then
    echo "Error: Flask is not installed. Installing..."
    pip install flask requests
fi

echo "All dependencies are installed!"
echo ""

# Function to cleanup background processes on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $RC_PID $SERVER_PID $MIDDLEWARE_PID 2>/dev/null
    wait $RC_PID $SERVER_PID $MIDDLEWARE_PID 2>/dev/null
    echo "All services stopped."
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start Registration Center
echo "Starting Registration Center on http://localhost:5000..."
python3 rc.py > rc.log 2>&1 &
RC_PID=$!
sleep 0.5

# Start Healthcare Server
echo "Starting Healthcare Server on http://localhost:5001..."
python3 server1.py > server.log 2>&1 &
SERVER_PID=$!
sleep 0.5

# Start Middleware with UI
echo "Starting Middleware & UI on http://localhost:8000..."
uvicorn middleware:app --host 0.0.0.0 --port 8000 > middleware.log 2>&1 &
MIDDLEWARE_PID=$!
sleep 1

echo ""
echo "=========================================="
echo "All services are running!"
echo "=========================================="
echo ""
echo "  Registration Center: http://localhost:5000"
echo "  Healthcare Server:   http://localhost:5001"
echo "  UI & Middleware:     http://localhost:8000"
echo ""
echo "Open http://localhost:8000 in your browser to use the UI"
echo ""
echo "Press Ctrl+C to stop all services"
echo "=========================================="
echo ""

# Keep the script running
wait
