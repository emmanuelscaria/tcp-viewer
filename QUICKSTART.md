# TCP Viewer - Quick Start Guide

## Prerequisites

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-venv python3-full nodejs npm
```

## Initial Setup

```bash
# Clone or navigate to the project
cd tcp-viewer

# Run setup script (as regular user, NOT with sudo)
./setup.sh
```

This will:
- Create Python virtual environment
- Install Python dependencies (grpcio, scapy, etc.)
- Generate gRPC stubs from .proto file

## Running the Application

### Terminal 1: Start Backend (requires root)

```bash
cd backend
sudo venv/bin/python3 server.py
```

You should see:
```
TCP Viewer gRPC Server started on port 50051
Note: Packet capture requires root/sudo privileges
Press Ctrl+C to stop
```

### Terminal 2: Start Frontend

```bash
cd frontend
npm start
```

The browser will automatically open at `http://localhost:3000`

You should see:
```
Compiled successfully!

You can now view tcp-viewer-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

## Testing

1. Click **"Start Monitoring"** button in the UI
2. Select interface (default: `lo` for loopback)
3. Generate some TCP traffic (e.g., browse websites, curl commands)
4. Watch packets appear in the Packet Stream
5. Click on connections to view detailed tcpcb metrics

## Troubleshooting

### Backend Issues

**Problem:** `Permission denied` when capturing packets
**Solution:** Make sure you're running with `sudo venv/bin/python3 server.py`

**Problem:** `ModuleNotFoundError: No module named 'scapy'`
**Solution:** Reinstall dependencies:
```bash
cd backend
venv/bin/pip install -r requirements.txt
```

### Frontend Issues

**Problem:** `react-scripts: not found`
**Solution:** Reinstall node modules:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Problem:** Port 3000 already in use
**Solution:** Kill existing process or use different port:
```bash
PORT=3001 npm start
```

## Development

### Backend Development
```bash
cd backend
source venv/bin/activate  # Activate venv for development
python3 server.py  # Run without sudo for testing (won't capture real packets)
```

### Frontend Development
- React app auto-reloads on file changes
- Current implementation uses simulated data
- To connect to real backend, implement gRPC-Web client (see frontend/README.md)

## Next Steps (Phase 2 & 3)

- [ ] Set up Envoy proxy for gRPC-Web
- [ ] Integrate pyroute2 for real socket statistics
- [ ] Add eBPF probes for kernel tcpcb introspection
- [ ] Implement filtering and search
- [ ] Add RTT time-series graphs
- [ ] Performance optimization for high packet rates

## Project Structure

```
tcp-viewer/
├── proto/                  # Protocol Buffer definitions
├── backend/               # Python gRPC server
│   ├── venv/             # Python virtual environment (auto-generated)
│   ├── server.py         # Main server
│   └── tcp_monitor_pb2*  # Generated gRPC stubs
├── frontend/             # React application
│   ├── src/              # React components
│   └── public/           # Static assets
└── setup.sh              # One-command setup script
```

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature-name`
6. Create Pull Request

## License

MIT License - See LICENSE file for details
