# Network Interface Configuration

## Default Interface: eth0

TCP Viewer now monitors **eth0** by default to capture real network traffic.

### Available Interfaces

Check your network interfaces:
```bash
ip link show
```

Common interfaces:
- **eth0** - Ethernet (wired network)
- **wlan0** - WiFi (wireless network)  
- **lo** - Loopback (localhost only, 127.0.0.1)
- **docker0** - Docker bridge
- **any** - All interfaces (captures everything)

### How to Change Interface

**Option 1: Change default in code**

Backend: Edit `backend/server_with_http.py`:
```python
start_packet_capture(interface='wlan0')  # Change to your interface
```

Frontend: Edit `frontend/src/App.js`:
```javascript
const [interface_, setInterface] = useState('wlan0');
```

**Option 2: Use 'any' to capture all interfaces**
```python
start_packet_capture(interface=None)  # Captures on all interfaces
```

**Option 3: Allow user selection in UI**

The interface dropdown in the UI allows selection, but currently it's not connected to the backend HTTP endpoint (only used for display). To make it functional, you would need to:
1. Add interface parameter to HTTP endpoint
2. Restart packet capture when interface changes
3. Or use multiple capture threads (one per interface)

### Current Setup

- **Backend**: Captures on `eth0`
- **Frontend**: Displays `eth0` in dropdown
- **Packets**: Real external network traffic
- **Loopback**: Not captured (use `lo` to see localhost traffic)

### Testing

After changing to eth0, restart backend and test:
```bash
cd ~/tcp-viewer/backend
sudo venv/bin/python3 server_with_http.py

# Generate external traffic
curl https://google.com
curl https://api.github.com

# Check captured packets
curl http://localhost:50052/api/traffic | jq '.packets[0:5]'
```

You should see real external IPs (not 127.0.0.1).

### Troubleshooting

**Problem**: No packets captured on eth0
**Solution**: Check if eth0 is up and has traffic
```bash
ip link show eth0
ifconfig eth0
tcpdump -i eth0 -c 5  # Verify packets exist
```

**Problem**: Permission denied
**Solution**: Run with sudo (packet capture requires root)
```bash
sudo venv/bin/python3 server_with_http.py
```

**Problem**: Interface not found
**Solution**: List available interfaces and use correct name
```bash
ip link show
# or
ifconfig -a
```
