# TCP Viewer - Fixes Applied

## Issues Fixed

### 1. Round-Trip Time (RTT) & Retransmission
**Problem:** RTT values were not being calculated from actual packet timing.

**Solution:**
- Implemented packet-based RTT calculation in `server.py`
- Track sent packets with timestamps
- Calculate RTT when ACKs are received
- Use exponential weighted moving average for SRTT (Smoothed RTT)
- Calculate RTO (Retransmission Timeout) based on SRTT and RTT variance
- Store RTT in microseconds for precision
- Display in frontend as milliseconds with proper formatting

### 2. Performance Insights
**Problem:** Metrics like Bandwidth-Delay Product and Theoretical Max Throughput were showing "N/A".

**Solution:**
- Calculate BDP as: `cwnd × MSS` (where MSS = 1460 bytes)
- Calculate throughput as: `(cwnd × MSS × 8) / RTT` in Mbps
- Update frontend to properly display these calculated values
- Show connection age based on timestamp

### 3. Recent Packets Section
**Problem:** Recent packets per connection were not being tracked or displayed.

**Solution:**
- Added `recent_packets` deque (max 10 packets) to each connection
- Store packet details: timestamp, direction, SEQ, ACK, flags
- Convert deque to list for JSON serialization
- Display in a formatted table in the frontend with:
  - Timestamp
  - Direction indicator (→ for outgoing, ← for incoming)
  - Sequence number
  - ACK number
  - TCP flags

## Technical Details

### Backend Changes (`server.py`)

1. **RTT Tracking:**
```python
# Track sent packets for RTT calculation
if is_outgoing and (len(tcp.payload) > 0 or tcp.flags.S or tcp.flags.F):
    monitor.sent_packets[conn_id][tcp.seq] = now
    
# Calculate RTT from ACKs
if not is_outgoing and tcp.flags.A:
    # Match ACK to sent packet
    # Calculate sample RTT
    # Update SRTT using exponential weighted moving average
```

2. **Recent Packets Storage:**
```python
pkt_record = {
    'timestamp': packet_data['timestamp'],
    'direction': 'outgoing' if is_outgoing else 'incoming',
    'seq': tcp.seq,
    'ack': tcp.ack if tcp.flags.A else 0,
    'flags': 'SAFR'...  # Compact flag representation
}
conn['recent_packets'].append(pkt_record)
```

3. **Congestion Window Estimation:**
- Based on inflight packets
- Estimated as: `min(inflight * 2, window // 1460)`
- Dynamically updated as packets are sent/acked

### Frontend Changes (`App.js`)

1. **RTT Display:**
- Show SRTT in microseconds with color coding
- Show RTT in milliseconds for readability
- Display RTO value
- Categorize latency (Excellent/Good/Fair/High)

2. **Performance Metrics:**
- Bandwidth-Delay Product calculation
- Theoretical Max Throughput calculation
- Proper formatting with `formatBytes()` and proper units

3. **Recent Packets Table:**
- 5-column table with proper formatting
- Direction arrows with colors
- Monospace font for numbers
- Timestamp formatting

## How to Test

1. **Start the backend:**
```bash
cd /home/escaria/tcp-viewer/backend
sudo venv/bin/python3 server.py
```

2. **Start the frontend:**
```bash
cd /home/escaria/tcp-viewer/frontend
npm start
```

3. **Generate TCP traffic:**
```bash
# Simple test
curl http://www.google.com

# Continuous traffic
while true; do curl -s http://www.google.com > /dev/null; sleep 1; done
```

4. **Or use the test script:**
```bash
./test_tcp_viewer.sh
```

## Expected Results

### Active Connections Table
- Shows all TCP connections with state, bytes sent/received
- Click on a connection to see details

### Connection Details Panel

#### RTT Section
- **Smoothed RTT:** Displayed in microseconds (e.g., "15234 µs")
- **RTT (Milliseconds):** Same value in ms for readability (e.g., "15.234 ms")
- **RTO:** Retransmission timeout (e.g., "1000 ms")
- **Latency Category:** Visual indicator with emoji (🟢/🟡/🔴)

#### Performance Insights
- **Bandwidth-Delay Product:** Based on cwnd × MSS
- **Theoretical Max Throughput:** Calculated as (cwnd × MSS × 8) / RTT
- **Connection Age:** Time since first packet

#### Recent Packets
- Table showing last 10 packets for the connection
- Columns: Time, Direction, SEQ, ACK, Flags
- Different colors for outgoing (blue arrow) vs incoming (green arrow)

## Verification

To verify the fixes are working, check that:

1. ✅ RTT values update as traffic flows
2. ✅ Performance metrics show realistic throughput calculations
3. ✅ Recent packets table populates with packet details
4. ✅ All values update in real-time
5. ✅ No "N/A" values when connections are active

## Known Limitations

- RTT calculation requires bidirectional traffic (need ACKs)
- Window size estimation is approximate (not reading kernel directly)
- libpcap warning can be ignored (using Scapy's Python-based capture)
- Requires root privileges for packet capture
