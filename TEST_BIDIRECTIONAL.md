# Testing Bidirectional Connection Tracking

## What Changed

TCP Viewer now tracks connections **bidirectionally**:

**Before:**
- `127.0.0.1:54321 → 127.0.0.1:443` = Connection A
- `127.0.0.1:443 → 127.0.0.1:54321` = Connection B
- Result: 2 separate connections in UI

**After:**
- `127.0.0.1:54321 ↔ 127.0.0.1:443` = One connection
- Both directions merged
- Result: 1 connection in UI with combined stats

## How to Test

1. **Restart the backend**:
```bash
cd ~/tcp-viewer/backend
# Press Ctrl+C to stop current server
sudo venv/bin/python3 server_with_http.py
```

2. **Generate bidirectional traffic**:
```bash
curl https://google.com
curl http://localhost:3000
```

3. **Check connections**:
```bash
curl http://localhost:50052/api/traffic | jq '.connections'
```

You should see:
- **Fewer total connections** (merged bidirectional flows)
- **bytes_sent** and **bytes_received** both populated
- Same connection ID for packets in both directions

## Technical Details

**Connection ID Generation:**
```python
# Sort endpoints so order doesn't matter
endpoints = sorted([
    (src_ip, src_port),
    (dst_ip, dst_port)
])
conn_id = MD5(f"{endpoints[0]}-{endpoints[1]}")
```

**Example:**
- Packet 1: `192.168.1.100:54321 → 93.184.216.34:443`
- Packet 2: `93.184.216.34:443 → 192.168.1.100:54321`
- Both get ID: `8cd1059887c96316`

**Byte Tracking:**
- `bytes_sent`: Data from lower endpoint to higher
- `bytes_received`: Data from higher endpoint to lower
- Direction determined by comparing to sorted endpoints

## Visualization in UI

The frontend will now show:
- One connection entry instead of two
- Total bidirectional traffic
- More accurate representation of actual TCP sessions
