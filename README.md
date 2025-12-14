# TCP Viewer

A network analysis tool for visualizing TCP traffic and kernel connection states in real-time.

## Architecture

- **Backend**: Python gRPC server with raw socket/Scapy packet capture
- **Frontend**: React.js dashboard with real-time updates
- **Protocol**: gRPC with Protocol Buffers for efficient streaming

## Project Structure

```
tcp-viewer/
├── proto/               # Protocol Buffer definitions
│   └── tcp_monitor.proto
├── backend/            # Python gRPC server
│   ├── server.py
│   ├── requirements.txt
│   ├── generate_grpc.sh
│   └── README.md
└── frontend/           # React.js UI
    ├── src/
    ├── public/
    ├── package.json
    └── README.md
```

## Quick Start

### 1. Setup Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Generate gRPC stubs
./generate_grpc.sh

# Run server (requires root)
sudo venv/bin/python3 server.py
```

The server runs on port 50051 (requires root for packet capture).

### 2. Setup Frontend

**Prerequisites**: Install Node.js and npm first
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm
```

Then:
```bash
cd frontend
npm install
npm start
```

The UI opens at `http://localhost:3000`

## Features

### Phase 1: The Sniffer ✅
- Raw TCP packet capture using Scapy
- gRPC server-side streaming
- React UI with live packet display
- Basic connection tracking

### Phase 2: The Introspector (Planned)
- Real kernel tcpcb introspection via eBPF/netlink
- Advanced connection state monitoring
- Historical data tracking

### Phase 3: The Visualizer (Planned)
- RTT and window size graphs
- Advanced filtering (IP, port, flags)
- Connection flow diagrams

## Technical Details

### gRPC Service

The `TcpMonitor` service provides a single streaming RPC:

```protobuf
rpc StreamTraffic (MonitorRequest) returns (stream TcpEvent);
```

Events include:
- **PacketInfo**: Individual TCP packet headers and flags
- **ConnectionStats**: Aggregated connection statistics and tcpcb data

### Requirements

- **OS**: Ubuntu 20.04+ (Kernel 5.4+)
- **Python**: 3.8+
- **Node.js**: 16+ (for frontend)
- **Permissions**: Root access for packet capture

## Development Notes

### Current Limitations

1. **Frontend-Backend Connection**: Currently uses simulated data. Full gRPC-Web integration requires Envoy proxy.
2. **tcpcb Values**: Backend returns mock values. Phase 2 will integrate pyroute2/eBPF for real kernel data.
3. **Performance**: Not yet optimized for high packet rates (>1000 pps).

### Next Steps

1. Set up Envoy proxy for gRPC-Web bridging
2. Generate JavaScript gRPC client stubs
3. Integrate pyroute2 for socket statistics
4. Add eBPF probes for deep kernel introspection

## License

MIT

## Contributing

This is a demonstration project based on the provided PRD. Contributions welcome for:
- eBPF integration
- Performance optimization  
- Additional visualizations
- Cross-platform support

---

**Note**: This tool requires privileged access to capture packets. Use responsibly and only on networks you own or have permission to monitor.
