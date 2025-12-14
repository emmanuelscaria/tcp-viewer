# Connecting Frontend to Real Backend Data

The frontend was initially showing **simulated data** because browsers cannot speak native gRPC directly. 

## Quick Solution: HTTP Bridge

I've created `server_with_http.py` which adds an HTTP endpoint alongside the gRPC server.

### How to Use Real Data:

**1. Stop the old backend** (if running):
```bash
sudo pkill -f "server.py"
```

**2. Start the new backend with HTTP bridge**:
```bash
cd backend
sudo venv/bin/python3 server_with_http.py
```

You should see:
```
✅ TCP Viewer gRPC Server started on port 50051
✅ HTTP Bridge started on port 50052
   Access: http://localhost:50052/api/traffic
```

**3. The frontend is already updated** - just reload the page or it will auto-reload

**4. Generate TCP traffic to see real packets**:
```bash
# In another terminal
curl https://api.github.com/repos/torvalds/linux
curl https://google.com
wget https://example.com
```

### What Changed:

**Backend (`server_with_http.py`)**:
- Runs gRPC server on port 50051 (for future gRPC-Web clients)
- Runs HTTP server on port 50052 (for current browser access)
- Endpoint: `GET http://localhost:50052/api/traffic`
- Returns JSON with real packets and connections

**Frontend (`App.js`)**:
- Removed simulated data generator
- Polls HTTP endpoint every second
- Displays real TCP packets captured by Scapy

### Testing:

```bash
# Test the HTTP endpoint directly
curl http://localhost:50052/api/traffic | jq .

# You should see real packet data like:
{
  "packets": [
    {
      "timestamp": "2025-12-14T07:30:00",
      "src_ip": "127.0.0.1",
      "src_port": 3000,
      "dst_ip": "127.0.0.1",
      "dst_port": 60786,
      "flag_ack": true,
      ...
    }
  ],
  "connections": [
    {
      "connection_id": "74ef1764114a8777",
      "state": "ESTABLISHED",
      ...
    }
  ]
}
```

### Future: Proper gRPC-Web (Phase 2)

For production, you should use:
1. Envoy proxy to bridge gRPC → gRPC-Web
2. Generated JavaScript gRPC client
3. Real-time streaming instead of polling

See `envoy.yaml` and `frontend/README.md` for details.
