#!/bin/bash
# Quick start script for TCP Viewer

echo "========================================="
echo "TCP Viewer - Quick Start"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  Warning: Backend packet capture requires root privileges"
    echo "   You'll need to run the backend with sudo separately"
fi

echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if Python dependencies are installed
if ! python3 -c "import grpc" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Generate gRPC stubs if not present
if [ ! -f "tcp_monitor_pb2.py" ]; then
    echo "Generating gRPC stubs..."
    ./generate_grpc.sh
fi

echo ""
echo "Backend setup complete!"
echo "Virtual environment created at: backend/venv"
echo ""
echo "========================================="
echo "To start the TCP Viewer:"
echo "========================================="
echo ""
echo "1. Start the backend (requires root):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   sudo venv/bin/python3 server.py"
echo ""
echo "2. Start the frontend (in another terminal):"
echo "   cd frontend"
echo "   npm install    # First time only"
echo "   npm start"
echo ""
echo "3. (Optional) Start Envoy proxy for gRPC-Web:"
echo "   docker run -d -p 8080:8080 -v $(pwd)/envoy.yaml:/etc/envoy/envoy.yaml envoyproxy/envoy:v1.24-latest"
echo ""
echo "========================================="
echo "Access the UI at: http://localhost:3000"
echo "========================================="
