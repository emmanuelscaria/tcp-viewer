# Testing TCP Viewer

## Start Backend

```bash
cd backend
sudo ./run_server.sh
```

Expected output:
```
==================================================
TCP Viewer - Fixed Backend
==================================================
✅ HTTP API on port 50052
   http://localhost:50052/api/traffic
   http://localhost:50052/api/stats (debug)

🔍 Capturing on eth0...

Press Ctrl+C to stop
```

## Start Frontend

In a new terminal:
```bash
cd frontend  
npm start
```

Opens browser at http://localhost:3000

## Generate Test Traffic

### Method 1: Using test scripts

Terminal 1:
```bash
python3 tcp_test_server.py
```

Terminal 2:
```bash
python3 tcp_test_client.py
```

### Method 2: curl to external site

```bash
curl https://example.com
curl https://github.com
```

### Method 3: Check the backend itself

```bash
curl http://localhost:50052/api/stats
```

This generates TCP traffic to localhost that will be captured!

## Verify Data

### Check Backend Statistics

```bash
curl http://localhost:50052/api/stats | jq .
```

Should show:
```json
{
  "total_packets": 123,
  "total_connections": 5,
  "connection_ids": ["abc123", "def456", ...]
}
```

### Check Traffic Data

```bash
curl http://localhost:50052/api/traffic | jq . | head -100
```

Should show packets and connections.

### Check Frontend

Open http://localhost:3000 and you should see:
1. **Packet Stream** (top) - scrolling list of recent packets
2. **Active Connections** (middle) - table of tracked TCP connections  
3. **Connection Details** (bottom) - detailed stats for selected connection

## Troubleshooting

**No packets showing:**
- Ensure backend is running as root
- Check interface name matches (default: eth0)
- Generate traffic using curl or test scripts

**Active Connections table empty:**
- This was fixed in the latest version
- Ensure you're running the new server.py
- Check backend logs for errors

**Frontend connection error:**
- Verify backend is on port 50052: `curl http://localhost:50052/api/stats`
- Check browser console for errors
- Try refreshing the page

## What to Look For

### In Packet Stream
- Timestamp
- Source/Dest IP and Port
- TCP flags (SYN, ACK, FIN, etc.)
- Sequence and ACK numbers
- Payload length

### In Connection Table
- Connection ID (hash)
- Endpoints (IP:Port ↔ IP:Port)
- State (ESTABLISHED, SYN_SENT, etc.)
- Bytes sent/received
- Packet count

### In Connection Details  
- TCP State
- Congestion window (snd_cwnd)
- Send/Receive windows
- Recent sequence numbers
- RTT estimate
- Last timestamp

## Success Criteria

✅ Backend captures packets without errors  
✅ Frontend shows packet stream updating  
✅ Active connections table populates with flows  
✅ Clicking a connection shows detailed stats  
✅ TCP state transitions visible (SYN→ESTABLISHED→FIN_WAIT)  
✅ Byte counters increment with traffic  
