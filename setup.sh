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

# Check for python3-venv
if ! dpkg -l | grep -q python3-venv; then
    echo "⚠️  Warning: python3-venv not installed"
    echo "   Install with: sudo apt install python3-venv"
    echo ""
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

# Activate virtual environment and install dependencies
echo "Installing dependencies in virtual environment..."
venv/bin/pip install -q -r requirements.txt

# Generate gRPC stubs if not present
if [ ! -f "tcp_monitor_pb2.py" ]; then
    echo "Generating gRPC stubs..."
    venv/bin/python -m grpc_tools.protoc \
      -I../proto \
      --python_out=. \
      --grpc_python_out=. \
      ../proto/tcp_monitor.proto
    echo "✅ Generated gRPC Python stubs successfully!"
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

