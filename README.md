# TCP Viewer

**TCP Viewer** is a real-time network analysis tool that visualizes TCP traffic and connection states at the packet level. It provides deep insights into TCP flows by tracking individual packets and computing connection metrics like RTT, retransmissions, and throughput.

---

## 🎯 Features

### Packet-Level Analysis
- ✅ **Real-time TCP packet capture** on network interfaces (default: `eth0`)
- ✅ **Bidirectional connection tracking** - merges both directions into unified connections
- ✅ **TCP flag visualization** - SYN, ACK, FIN, RST, PSH, URG flags per packet
- ✅ **Packet stream display** - scrollable log with timestamps and headers

### Connection Intelligence
- ✅ **Active connection table** - grouped by 4-tuple (src_ip:port ↔ dst_ip:port)
- ✅ **TCP state tracking** - ESTABLISHED, SYN_SENT, FIN_WAIT, etc.
- ✅ **Traffic statistics** - sent/received bytes and packet counts per direction
- ✅ **Round-Trip Time (RTT) estimation** - calculated from SYN-SYNACK and data-ACK pairs
- ✅ **Retransmission detection** - tracks duplicate sequence numbers
- ✅ **Recent packet history** - last 5 packets per connection with seq/ack numbers

### Performance Metrics
- ✅ **Throughput calculation** - bytes/sec for each direction
- ✅ **Window size tracking** - current TCP window from packet headers
- ✅ **Sequence number monitoring** - tracks latest seq/ack values
- ✅ **Connection duration** - elapsed time since first packet

---

## 🏗️ Architecture

### System Design

```
┌─────────────────────────────────────────┐
│         Frontend (React.js)             │
│  - Dashboard with live updates          │
│  - Connection table & packet stream     │
│  - Auto-refresh every 1 second          │
└─────────────┬───────────────────────────┘
              │ HTTP GET /api/traffic
              │ (JSON polling)
┌─────────────▼───────────────────────────┐
│      Backend (Python HTTP Server)       │
│  - REST API on port 50052               │
│  - In-memory packet/connection storage  │
│  - Thread-safe data structures          │
└─────────────┬───────────────────────────┘
              │ Scapy sniff()
┌─────────────▼───────────────────────────┐
│       Network Interface (eth0)          │
│  - Raw packet capture (requires root)   │
│  - Filters TCP traffic only             │
└──────────────────────────────────────────┘
```

### Component Breakdown

#### Backend (`/backend`)
- **`server.py`** - HTTP REST API server + packet capture orchestrator
  - Runs on `http://localhost:50052`
  - Endpoint: `GET /api/traffic` returns JSON with packets & connections
  - Thread-safe in-memory storage with locks
  
- **`tcp_packet_analyzer.py`** - Packet processing engine
  - Extracts IP/TCP headers using Scapy
  - Computes connection ID from 4-tuple
  - Bidirectional flow normalization
  - RTT calculation from packet timing
  
- **`tcp_introspector.py`** - Connection state enrichment
  - Reads `/proc/net/tcp` for kernel-level state
  - Maps connections to TCP states (ESTABLISHED, etc.)
  - Fallback to packet-based state inference

#### Frontend (`/frontend`)
- **`src/App.js`** - React dashboard component
  - **Packet Stream Panel** - Live scrolling packet log
  - **Active Connections Table** - Clickable connection rows
  - **Connection Details Panel** - Expanded metrics for selected connection
  - Auto-refresh via `setInterval` polling

---

## 🚀 Quick Start

### Prerequisites
- **OS**: Ubuntu 20.04+ (tested on 22.04)
- **Python**: 3.8+
- **Node.js**: 14+
- **Permissions**: Root/sudo for packet capture

### Installation

#### 1. Clone Repository
```bash
git clone https://github.com/emmanuelscaria/tcp-viewer.git
cd tcp-viewer
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install
```

### Running the Application

#### Terminal 1: Start Backend (requires sudo)
```bash
cd backend
sudo venv/bin/python3 server.py
```

**Expected output:**
```
=========================================
TCP Viewer - Backend Server
=========================================

✅ HTTP REST API started on port 50052
   Access: http://localhost:50052/api/traffic

🔍 Starting packet capture on interface: eth0

Note: Packet capture requires root/sudo privileges
Press Ctrl+C to stop
```

#### Terminal 2: Start Frontend
```bash
cd frontend
npm start
```

**The UI will open at:** `http://localhost:3000`

---

## 🧪 Testing

### Option 1: Test Scripts (Loopback)
```bash
# Terminal 1: Start test server
python3 ../tcp_test_server.py

# Terminal 2: Start test client
python3 ../tcp_test_client.py
```

### Option 2: Real Traffic (Internet)
```bash
# Generate HTTPS traffic
curl https://www.google.com

# Generate persistent connection
curl -H "Connection: keep-alive" https://github.com

# Download large file
wget https://speed.hetzner.de/100MB.bin
```

### Option 3: Custom Connection Script
```bash
# Long-lived TCP connection
./test_tcp_connection.sh
```

---

## 📊 Data Flow

### Packet Capture Pipeline
```
1. Scapy sniffs raw packets on eth0
2. Filter: TCP packets only (IP layer + TCP layer)
3. Extract: IP headers (src, dst) + TCP headers (sport, dport, flags, seq, ack, win)
4. Normalize: Create bidirectional connection ID
5. Calculate: RTT from timestamp differences
6. Store: Add to in-memory packet buffer (max 1000)
7. Update: Merge into connection state
```

### Connection Tracking
```
Connection ID = hash(sorted([
  (src_ip, src_port),
  (dst_ip, dst_port)
]))

State = {
  connection_id,
  src_ip, src_port,
  dst_ip, dst_port,
  state (from /proc/net/tcp or packet flags),
  bytes_sent, bytes_received,
  packets_sent, packets_received,
  rtt_ms (smoothed),
  retransmissions,
  window_size,
  last_seq, last_ack,
  recent_packets: [last 5 packets]
}
```

---

## 📁 Project Structure

```
tcp-viewer/
├── backend/
│   ├── server.py                 # Main HTTP server + packet capture
│   ├── tcp_packet_analyzer.py    # Packet processing logic
│   ├── tcp_introspector.py       # /proc/net/tcp reader
│   ├── requirements.txt          # Python dependencies
│   ├── run_server.sh             # Startup script
│   └── venv/                     # Virtual environment
│
├── frontend/
│   ├── src/
│   │   ├── App.js                # Main React component
│   │   ├── App.css               # Styles
│   │   └── index.js              # React entry point
│   ├── public/
│   ├── package.json              # Node dependencies
│   └── node_modules/
│
├── README.md                     # This file
├── QUICKSTART.md                 # Step-by-step guide
├── TCP_METRICS_GUIDE.md          # Metrics documentation
├── TESTING.md                    # Testing procedures
├── setup.sh                      # Automated setup script
├── tcp_test_server.py            # Test TCP server
└── tcp_test_client.py            # Test TCP client
```

---

## 🔧 Configuration

### Change Network Interface
Edit `backend/server.py`:
```python
INTERFACE = 'eth0'  # Change to 'wlan0', 'lo', etc.
```

### Adjust Packet Buffer Size
```python
self.max_packets = 1000  # Increase for more history
```

### Change Polling Interval (Frontend)
Edit `frontend/src/App.js`:
```javascript
setInterval(fetchTraffic, 1000);  // Change to 500 for faster updates
```

---

## 🐛 Troubleshooting

### No Packets Captured
- **Check interface**: `ip link show` - ensure `eth0` is up
- **Verify traffic**: `sudo tcpdump -i eth0 -c 10`
- **Permissions**: Must run backend with `sudo`

### libpcap Warning
```
ERROR: Cannot set filter: libpcap is not available
```
**Solution**: Install libpcap
```bash
sudo apt-get install libpcap-dev
pip install --upgrade scapy
```

### Frontend Shows Empty Tables
- **Check backend**: Visit `http://localhost:50052/api/traffic`
- **CORS**: Ensure backend serves CORS headers (already configured)
- **Browser console**: Check for fetch errors (F12)

### Connection Not Detected
- **Loopback issue**: Change interface to `lo` for local traffic
- **External traffic**: Use `eth0` or `wlan0`
- **Firewall**: Check `sudo iptables -L`

---

## 📚 Technical Details

### RTT Calculation
```python
# Method 1: SYN-SYNACK handshake
if packet.flags == SYN:
    sent_time[seq] = timestamp
if packet.flags == SYN+ACK:
    rtt = timestamp - sent_time[ack-1]

# Method 2: Data-ACK pairs
if packet.payload > 0:
    sent_time[seq] = timestamp
if packet.flags == ACK:
    rtt = timestamp - sent_time[ack]
```

### Retransmission Detection
```python
if seq in seen_sequences[connection_id]:
    retransmissions += 1
```

### State Inference (without kernel)
```python
if SYN and not ACK: state = "SYN_SENT"
if SYN and ACK: state = "SYN_RECEIVED"
if FIN: state = "FIN_WAIT"
else: state = "ESTABLISHED"
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- eBPF integration for zero-copy packet capture
- WebSocket streaming (replace polling)
- Packet filtering UI (by port, IP, flags)
- Export to PCAP
- TCP congestion window visualization

---

## 📝 License

MIT License - see LICENSE file

---

## 🙏 Acknowledgments

- **Scapy**: Packet manipulation library
- **React**: Frontend framework
- **Linux Kernel**: `/proc/net/tcp` interface

---

**Author**: Emmanuel Scaria  
**Repository**: https://github.com/emmanuelscaria/tcp-viewer  
**Version**: 1.0.0  
**Last Updated**: December 14, 2025
