# TCP Viewer - Backend

Python gRPC server for TCP packet capture and kernel introspection.

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

3. Generate gRPC stubs:
```bash
chmod +x generate_grpc.sh
./generate_grpc.sh
```

4. Run the server (requires root):
```bash
# Option 1: Keep venv activated and use sudo -E
sudo -E venv/bin/python3 server.py

# Option 2: Direct path to venv python
sudo venv/bin/python3 server.py
```

## Architecture

- **server.py**: Main gRPC server implementation
- **tcp_monitor_pb2.py**: Auto-generated Protocol Buffer messages (generated)
- **tcp_monitor_pb2_grpc.py**: Auto-generated gRPC service stubs (generated)

## Phase 1 Features

- ✅ Raw packet capture using Scapy
- ✅ gRPC server-side streaming
- ✅ Basic connection tracking
- ⚠️ Mock tcpcb values (Phase 2 will integrate real kernel data via eBPF/netlink)

## Next Steps (Phase 2)

- Integrate pyroute2 for real socket statistics
- Add eBPF probes for deep tcpcb introspection
- Implement proper connection cleanup and timeouts
