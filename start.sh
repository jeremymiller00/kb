#!/bin/bash

echo "Starting Knowledge Base application..."

# Check if postgres is running, start if not
# Not using for now since pg is managed by mac app
# if ! brew services list | grep postgresql | grep started > /dev/null; then
#     echo "Starting PostgreSQL..."
#     brew services start postgresql
# else
#     echo "PostgreSQL already running"
# fi

# # Wait a moment for postgres to start
# sleep 2

# Start FastAPI backend
echo "Starting FastAPI backend..."
python src/app.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Kill any existing process on port 5001
if lsof -ti :5001 > /dev/null 2>&1; then
    echo "Killing existing process on port 5001..."
    kill -9 $(lsof -ti :5001) 2>/dev/null
    sleep 1
fi

# Start FastHTML UI
echo "Starting FastHTML UI..."
uvicorn ui:app --reload --host 0.0.0.0 --port 5001 &
UI_PID=$!

echo ""
echo "🚀 All services started!"
echo "📊 FastAPI backend: http://127.0.0.1:8000"
echo "🌐 FastHTML UI: http://0.0.0.0:5001"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID 2>/dev/null
    kill $UI_PID 2>/dev/null
    echo "Services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait