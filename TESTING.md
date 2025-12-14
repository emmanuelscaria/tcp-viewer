# TCP Viewer - Testing Guide

## Quick Start

### 1. Restart the Backend

```bash
cd ~/tcp-viewer/backend

# Stop any existing server
sudo pkill -f server_with_http.py

# Start the server (requires sudo for packet capture)
sudo venv/bin/python3 server_with_http.py
```

You should see output like:
```
✅ TCP Viewer gRPC Server started on port 50051
✅ HTTP Bridge started on port 50052
   Access: http://localhost:50052/api/traffic
📡 Sniffing on interface: eth0
```

### 2. Generate Test Traffic

In another terminal:

```bash
# Simple test - make some web requests
curl http://www.google.com
curl http://www.github.com
curl http://www.example.com

# Or use the test script
/tmp/test_tcp.sh
```

### 3. Verify Backend is Capturing

```bash
# Check if packets and connections are being captured
curl http://localhost:50052/api/traffic | python3 -m json.tool | head -50
```

You should see:
- `packets`: array with recent TCP packets
- `connections`: array with active TCP connections

### 4. Start the Frontend

In another terminal:

```bash
cd ~/tcp-viewer/frontend
npm start
```

Then open http://localhost:3000 in your browser.

Click "Start Monitoring" to begin viewing traffic.

## Debugging

### Check if backend is running
```bash
curl http://localhost:50052/api/traffic
```

### Check backend logs
The server prints debug messages:
- `🆕 New connection: ...` when a new TCP connection is detected
- `📊 Updated connection ...` when connection stats are updated
- `📡 Sniffing on interface: ...` when packet capture starts

### Common Issues

1. **No packets captured**
   - Make sure you're running the server with `sudo`
   - Check that eth0 interface exists: `ip link show eth0`
   - Try generating traffic: `curl http://www.google.com`

2. **No connections showing in frontend**
   - Check browser console for errors
   - Verify API is returning connections: `curl http://localhost:50052/api/traffic`
   - Make sure you clicked "Start Monitoring" button

3. **Frontend shows "Disconnected"**
   - Backend might not be running
   - Check if port 50052 is accessible: `curl http://localhost:50052/api/traffic`

## Architecture

```
┌──────────────┐         HTTP Poll          ┌─────────────┐
│              │ ◄─────(every 1 sec)────────│             │
│   Backend    │                             │  Frontend   │
│ (Python +    │                             │  (React)    │
│  Scapy)      │                             │             │
│              │                             │             │
│ Port: 50052  │                             │ Port: 3000  │
└──────┬───────┘                             └─────────────┘
       │
       │ Packet Capture
       ▼
  ┌────────────┐
  │   eth0     │
  │ Interface  │
  └────────────┘
```

## TCP Metrics Explained

The application now **calculates TCP metrics from packet data** instead of reading kernel state.

### Metrics Displayed:

- **State**: TCP connection state (SYN_SENT, ESTABLISHED, FIN_WAIT, etc.) - derived from packet flags
- **RTT (Round Trip Time)**: Calculated by measuring time between DATA packet and corresponding ACK
- **Smoothed RTT (srtt)**: Exponentially weighted moving average of RTT samples
- **RTO (Retransmission Timeout)**: Calculated as SRTT + 4×RTT_variation (bounds: 200ms - 60s)
- **Congestion Window (cwnd)**: Estimated from number of inflight (unacknowledged) packets
- **Slow Start Threshold (ssthresh)**: Estimated threshold, reduced on retransmissions
- **Send/Receive Window**: Advertised window sizes from TCP headers
- **Bytes Sent/Received**: Cumulative payload bytes in each direction
- **Inflight Packets**: Current count of sent but unacknowledged segments
- **Retransmissions**: Count of detected retransmitted packets

### How Metrics are Calculated:

1. **RTT Measurement**: 
   - Track sequence numbers and timestamps of outgoing packets
   - When ACK arrives, calculate time delta from corresponding sent packet
   - Apply exponential smoothing: SRTT = 0.875×SRTT + 0.125×sample

2. **cwnd Estimation**:
   - Count unacknowledged packets (inflight)
   - During slow start: cwnd doubles when all packets acked
   - During congestion avoidance: cwnd grows linearly
   - On retransmission: ssthresh = cwnd/2, cwnd = ssthresh

3. **Retransmission Detection**:
   - Packet with sequence number less than previously sent = retransmission

### Testing Packet-Based Metrics:

```bash
# Run the test client to generate measurable traffic
python3 ~/tcp_test_client.py

# This creates persistent HTTP connection with example.com
# You should see RTT measurements appear after first request-response
```

**Note**: Packet-based metrics are approximations. For kernel-accurate values, compare with:
```bash
ss -ti | grep -A 10 "example.com"
```
