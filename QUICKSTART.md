# TCP Viewer - Quick Start Guide

**Get up and running in 5 minutes!**

---

## Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ or similar Linux distribution
- **Python**: 3.8 or higher
- **Node.js**: 14.x or higher (with npm)
- **Root Access**: Required for packet capture

### Install Dependencies

```bash
# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y python3 python3-venv python3-full nodejs npm libpcap-dev

# Verify installations
python3 --version  # Should be 3.8+
node --version     # Should be 14+
npm --version
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/emmanuelscaria/tcp-viewer.git
cd tcp-viewer
```

### Step 2: Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Deactivate (we'll run with sudo later)
deactivate
```

**Expected output:**
```
Successfully installed scapy-2.5.0 pyroute2-0.7.12 ...
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node.js dependencies
npm install
```

**Expected output:**
```
added 1500 packages in 45s
```

---

## Running the Application

### Terminal 1: Start Backend

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

**⚠️ Important Notes:**
- Must use `sudo` for packet capture
- Default interface is `eth0` (can be changed in server.py)
- Backend stays running - don't close this terminal

### Terminal 2: Start Frontend

```bash
cd frontend
npm start
```

**Expected output:**
```
Compiled successfully!

You can now view tcp-viewer-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.
```

**Browser will auto-open to:** `http://localhost:3000`

---

## Using the Application

### 1. Verify Backend Connection

The UI should show:
- **Connection Status**: "Backend: Connected ✅"
- **Interface**: "Monitoring: eth0"

### 2. Generate Test Traffic

**Option A: Quick Test (Loopback)**
```bash
# Terminal 3
curl http://localhost:50052/api/traffic
```

**Option B: Real Internet Traffic**
```bash
# Terminal 3
curl https://www.google.com
curl https://github.com
wget https://httpbin.org/bytes/10000
```

**Option C: Test Scripts**
```bash
# Terminal 3: Start server
cd /path/to/tcp-viewer
python3 tcp_test_server.py

# Terminal 4: Start client
python3 tcp_test_client.py
```

### 3. Observe the UI

**Packet Stream Panel** (left side):
- Live scrolling log of TCP packets
- Shows timestamps, IPs, ports, flags

**Active Connections Table** (top right):
- One row per TCP connection
- Click any row to see details

**Connection Details Panel** (bottom):
- Detailed metrics for selected connection
- RTT, throughput, window sizes
- Recent packet history

---

## Testing Guide

### Loopback Traffic (Internal)

**Change interface to `lo` in `backend/server.py`:**
```python
INTERFACE = 'lo'  # Line ~20
```

**Then restart backend and test:**
```bash
curl http://localhost:50052/api/traffic
```

### External Traffic (Internet)

**Keep interface as `eth0` (or your active NIC):**
```bash
# Find your network interface
ip link show

# Update backend/server.py if needed
INTERFACE = 'wlan0'  # For WiFi
INTERFACE = 'ens33'  # For VMware
```

**Generate traffic:**
```bash
# HTTPS connection
curl https://www.google.com

# Persistent connection
curl -H "Connection: keep-alive" https://httpbin.org/delay/5

# Large download
wget https://speed.hetzner.de/10MB.bin
```

### Long-Lived Connections

**Use provided test script:**
```bash
./test_tcp_connection.sh
```

Or manually:
```bash
# Terminal A: Server
nc -l 8888

# Terminal B: Client  
nc localhost 8888
# Type messages and press Enter
```

---

## Troubleshooting

### Backend Issues

#### ❌ "Permission denied" Error
```
PermissionError: [Errno 1] Operation not permitted
```

**Solution**: Run with sudo
```bash
sudo venv/bin/python3 server.py
```

#### ❌ "ModuleNotFoundError: No module named 'scapy'"
**Solution**: Reinstall dependencies in venv
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

#### ❌ "Cannot set filter: libpcap not available"
**Solution**: Install libpcap
```bash
sudo apt install libpcap-dev
pip install --upgrade scapy
```

#### ❌ "No packets captured"
**Check 1**: Verify interface exists
```bash
ip link show  # Look for eth0, wlan0, etc.
```

**Check 2**: Verify interface has traffic
```bash
sudo tcpdump -i eth0 -c 10
```

**Check 3**: Try loopback interface
```python
# In backend/server.py
INTERFACE = 'lo'  # Change from 'eth0'
```

### Frontend Issues

#### ❌ "react-scripts: not found"
**Solution**: Reinstall node modules
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### ❌ Port 3000 already in use
**Solution**: Use different port
```bash
PORT=3001 npm start
```

Or kill existing process:
```bash
lsof -ti:3000 | xargs kill -9
```

#### ❌ "Failed to fetch" / No data in UI
**Check 1**: Verify backend is running
```bash
curl http://localhost:50052/api/traffic
```

**Check 2**: Check browser console (F12)
- Look for CORS errors
- Verify fetch requests succeed

**Check 3**: Generate some traffic
```bash
curl https://www.google.com  # Should appear in UI
```

### Common Workflow Issues

#### No connections showing up

**For localhost traffic**: Change interface to `lo`
```python
# backend/server.py
INTERFACE = 'lo'
```

**For internet traffic**: Use `eth0` or active interface
```bash
# Find active interface
ip route | grep default
```

#### Packets showing but connections empty

**Check**: Make sure packets have TCP layer
```bash
curl http://localhost:50052/api/traffic | jq '.packets[0]'
```

Should show `src_port`, `dst_port`, etc.

---

## Development Workflow

### Backend Development

**Run without sudo (limited functionality):**
```bash
cd backend
source venv/bin/activate
python3 server.py  # Won't capture packets, but API works
```

**Enable debug logging:**
```python
# Add to server.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test API endpoint:**
```bash
# Check if server responds
curl http://localhost:50052/api/traffic | jq .

# Watch for updates
watch -n 1 'curl -s http://localhost:50052/api/traffic | jq ".connections | length"'
```

### Frontend Development

**Fast refresh is enabled** - changes auto-reload

**Test UI without backend:**
```javascript
// Temporarily mock data in App.js
const [packets] = useState([
  {timestamp: "2025-12-14...", src_ip: "1.2.3.4", ...}
]);
```

**Build for production:**
```bash
npm run build
# Output: build/ folder
```

---

## Advanced Configuration

### Change Network Interface

**Edit `backend/server.py`:**
```python
INTERFACE = 'wlan0'  # For WiFi
INTERFACE = 'ens33'  # For VMware
INTERFACE = 'lo'     # For loopback testing
```

### Increase Packet Buffer

**Edit `backend/server.py`:**
```python
self.max_packets = 5000  # Default is 1000
```

### Faster UI Updates

**Edit `frontend/src/App.js`:**
```javascript
setInterval(fetchTraffic, 500);  // Default is 1000ms
```

**⚠️ Warning**: Lower intervals = higher CPU usage

### Change Backend Port

**Edit `backend/server.py`:**
```python
PORT = 8080  # Default is 50052
```

**Update frontend fetch URL:**
```javascript
// frontend/src/App.js
fetch('http://localhost:8080/api/traffic')
```

---

## Performance Tips

### For High Traffic Networks

1. **Filter specific ports** (edit `server.py`):
```python
# Only capture HTTPS traffic
filter_bpf = "tcp port 443"
sniff(filter=filter_bpf, ...)
```

2. **Reduce packet history**:
```python
self.max_packets = 100  # Keep fewer packets
```

3. **Disable recent packets** (saves memory):
```python
# In tcp_packet_analyzer.py
# Comment out recent_packets tracking
```

### For Low-End Systems

1. **Increase polling interval**:
```javascript
setInterval(fetchTraffic, 2000);  // Every 2 seconds
```

2. **Limit connection count**:
```python
# Keep only top 50 connections by activity
connections = sorted(...)[:50]
```

---

## Next Steps

### Explore Features
✅ Click different connections in the table  
✅ Observe RTT changes over time  
✅ Generate traffic and watch retransmissions  
✅ Compare sent vs received bytes

### Read Documentation
- **README.md** - Full feature overview
- **ARCHITECTURE.md** - System design details  
- **TCP_METRICS_GUIDE.md** - Understanding the metrics
- **TESTING.md** - Comprehensive test scenarios

### Contribute
- Report bugs: GitHub Issues
- Suggest features: Pull Requests
- Ask questions: Discussions

---

## Quick Reference

### Start Application
```bash
# Terminal 1
cd backend && sudo venv/bin/python3 server.py

# Terminal 2  
cd frontend && npm start
```

### Stop Application
```bash
# Backend: Ctrl+C in terminal
# Frontend: Ctrl+C in terminal
```

### Test Traffic
```bash
# Loopback
curl http://localhost:50052/api/traffic

# Internet
curl https://www.google.com
```

### Check Status
```bash
# Backend health
curl http://localhost:50052/api/traffic | jq '.connections | length'

# Frontend build
cd frontend && npm run build
```

---

**Need Help?**  
- 📧 Email: [your-email]
- 🐛 Issues: https://github.com/emmanuelscaria/tcp-viewer/issues
- 📖 Docs: /docs folder

**Happy Monitoring! 🚀**
