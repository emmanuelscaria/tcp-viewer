#!/bin/bash
# Quick start script for TCP Viewer

echo "========================================="
echo "TCP Viewer - Quick Start"
echo "========================================="
echo ""

# Don't run as root
if [ "$EUID" -eq 0 ]; then 
    echo "❌ Don't run this script with sudo"
    echo "   Run as regular user: ./setup.sh"
    echo "   (You'll use sudo only when starting the server)"
    exit 1
fi

# Check for python3-venv
if ! dpkg -l 2>/dev/null | grep -q python3-venv; then
    echo "⚠️  python3-venv not installed"
    echo "   Install with: sudo apt install python3-venv python3-full"
    echo ""
    exit 1
fi

echo "Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        echo "   Install with: sudo apt install python3-venv python3-full"
        cd ..
        exit 1
    fi
fi

# Check if pip is available in venv
if [ ! -f "venv/bin/pip" ]; then
    echo "❌ Virtual environment doesn't have pip"
    echo "   This usually means python3-venv is not fully installed"
    echo "   Install with: sudo apt install python3-venv python3-full"
    cd ..
    exit 1
fi

# Install dependencies
echo "Installing dependencies in virtual environment..."
venv/bin/pip install -q --upgrade pip
venv/bin/pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    cd ..
    exit 1
fi

# Generate gRPC stubs if not present
if [ ! -f "tcp_monitor_pb2.py" ]; then
    echo "Generating gRPC stubs..."
    venv/bin/python -m grpc_tools.protoc \
      -I../proto \
      --python_out=. \
      --grpc_python_out=. \
      ../proto/tcp_monitor.proto
    
    if [ $? -eq 0 ]; then
        echo "✅ Generated gRPC Python stubs successfully!"
    else
        echo "❌ Failed to generate gRPC stubs"
        cd ..
        exit 1
    fi
fi

cd ..

echo ""
echo "✅ Backend setup complete!"
echo "   Virtual environment: backend/venv"
echo ""
echo "========================================="
echo "To start the TCP Viewer:"
echo "========================================="
echo ""
echo "1. Start the backend (requires root):"
echo "   cd backend"
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

