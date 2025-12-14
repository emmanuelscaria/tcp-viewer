# TCP Viewer - Backend

Python HTTP REST API server for TCP packet capture and kernel introspection.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the server (requires root):
```bash
# Direct path to venv python
sudo venv/bin/python3 server.py
```

## Architecture

- **server.py**: Main HTTP REST API server
- **tcp_introspector.py**: Kernel TCP statistics via `ss` command
- **tcp_packet_analyzer.py**: Packet-level TCP analysis (RTT calculation, etc.)

## Features

- ✅ Raw packet capture using Scapy
- ✅ HTTP REST API on port 50052
- ✅ Real-time connection tracking (bidirectional)
- ✅ Kernel TCP statistics via pyroute2/ss
- ✅ Packet-level RTT calculation
- ✅ Per-connection packet history

## API Endpoints

**GET /api/traffic**
Returns JSON with current packets and active connections:
```json
{
  "packets": [...],
  "connections": [...]
}
```

## Notes

- Packet capture runs on **eth0** interface by default
- Requires root/sudo for packet capture
- Uses bidirectional connection IDs (A→B and B→A are the same connection)
