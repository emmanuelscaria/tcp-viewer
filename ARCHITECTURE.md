# TCP Viewer - Architecture Documentation

**Version**: 1.0  
**Last Updated**: December 14, 2025

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Implementation Details](#implementation-details)
5. [Performance Considerations](#performance-considerations)
6. [Future Enhancements](#future-enhancements)

---

## System Overview

TCP Viewer is a **client-server application** designed for real-time TCP traffic analysis on Linux systems. It combines low-level packet capture with high-level connection state tracking.

### Design Principles

1. **Simplicity over Complexity**: Uses HTTP/JSON instead of gRPC for easier debugging
2. **Real-time First**: Optimized for live monitoring, not historical analysis
3. **Minimal Dependencies**: Relies on standard Linux tools and libraries
4. **User-Friendly**: Web-based UI accessible via browser

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | React.js 18+ | Interactive web dashboard |
| **Transport** | HTTP/1.1 + JSON | Request/response API |
| **Backend** | Python 3.8+ | Packet processing & HTTP server |
| **Capture** | Scapy 2.5+ | Raw socket packet sniffing |
| **Kernel** | /proc/net/tcp | TCP connection state reading |

---

## Component Architecture

### 1. Backend (Python)

```
backend/
├── server.py                    # Main entry point
├── tcp_packet_analyzer.py       # Packet processing
└── tcp_introspector.py          # Kernel state reader
```

#### 1.1 Server Component (`server.py`)

**Responsibilities**:
- HTTP server on port 50052
- Thread-safe data storage
- Packet capture orchestration
- REST API endpoint

**Key Classes**:

```python
class TcpMonitor:
    """Central data store with thread-safe access"""
    - packets: List[Dict]          # Last 1000 packets
    - connections: Dict[str, Dict] # Active connections
    - lock: Lock                   # Thread synchronization
    - sent_packets: Dict           # For RTT calculation
```

```python
class RequestHandler(BaseHTTPRequestHandler):
    """HTTP request processor"""
    - GET /api/traffic -> JSON response
    - CORS headers enabled
    - Gzip compression
```

**Threading Model**:
```
Main Thread:  HTTP Server (blocking accept())
Worker Thread: Packet sniffer (scapy.sniff in background)
```

#### 1.2 Packet Analyzer (`tcp_packet_analyzer.py`)

**Responsibilities**:
- Parse raw packets into structured data
- Extract IP and TCP headers
- Calculate RTT from packet pairs
- Detect retransmissions

**Core Function**:
```python
def process_packet(packet) -> Tuple[packet_data, connection_data]:
    """
    Input: Scapy packet object
    Output: 
      - packet_data: Individual packet info
      - connection_data: Updated connection state
    """
```

**RTT Algorithm**:
```python
# Store outgoing packet timestamp
sent_packets[conn_id][seq] = timestamp

# When ACK arrives
if ack in sent_packets[conn_id]:
    rtt = current_time - sent_packets[conn_id][ack]
    smoothed_rtt = 0.875 * old_rtt + 0.125 * rtt  # EWMA
```

#### 1.3 TCP Introspector (`tcp_introspector.py`)

**Responsibilities**:
- Read `/proc/net/tcp` (IPv4) and `/proc/net/tcp6` (IPv6)
- Parse hex-encoded addresses and states
- Map kernel state codes to names

**State Mapping** (from Linux kernel):
```python
TCP_STATES = {
    0x01: "ESTABLISHED",
    0x02: "SYN_SENT",
    0x03: "SYN_RECV",
    0x04: "FIN_WAIT1",
    # ... etc
}
```

### 2. Frontend (React)

```
frontend/src/
├── App.js       # Main dashboard component
├── App.css      # Styles
└── index.js     # React entry point
```

#### 2.1 Component Structure

```jsx
<App>
  ├── <Header />
  ├── <PacketStreamPanel>
  │   └── <PacketTable />
  │       └── rows: packets[]
  ├── <ConnectionsPanel>
  │   └── <ConnectionTable>
  │       └── rows: connections[]
  │           └── onClick -> setSelectedConnection()
  └── <ConnectionDetailsPanel>
      ├── connection: selectedConnection
      ├── <StateInfo />
      ├── <TrafficStats />
      ├── <RTTMetrics />
      └── <RecentPackets />
```

#### 2.2 Data Fetching

```javascript
// Polling mechanism
useEffect(() => {
  const fetchTraffic = async () => {
    const response = await fetch('http://localhost:50052/api/traffic');
    const data = await response.json();
    setPackets(data.packets);
    setConnections(Object.values(data.connections));
  };

  fetchTraffic(); // Initial fetch
  const interval = setInterval(fetchTraffic, 1000);
  return () => clearInterval(interval);
}, []);
```

#### 2.3 State Management

```javascript
// React hooks for state
const [packets, setPackets] = useState([]);
const [connections, setConnections] = useState([]);
const [selectedConnection, setSelectedConnection] = useState(null);
```

---

## Data Flow

### End-to-End Packet Journey

```
1. Network Interface (eth0)
   ↓ Raw Ethernet frames
   
2. Scapy Sniffer (BPF filter: TCP only)
   ↓ Scapy Packet object
   
3. process_packet() [tcp_packet_analyzer.py]
   ↓ packet_data + connection_data
   
4. TcpMonitor.add_packet_and_update_connection()
   ↓ Stored in memory (with lock)
   
5. HTTP GET /api/traffic
   ↓ JSON serialization
   
6. Frontend fetch()
   ↓ React state update
   
7. Re-render UI components
```

### Data Structures

#### Packet Format (JSON)
```json
{
  "timestamp": "2025-12-14T12:34:56.789012",
  "src_ip": "192.168.1.10",
  "src_port": 54321,
  "dst_ip": "93.184.216.34",
  "dst_port": 443,
  "flag_syn": false,
  "flag_ack": true,
  "flag_fin": false,
  "flag_rst": false,
  "flag_psh": true,
  "flag_urg": false,
  "payload_length": 1460,
  "seq_num": 1234567890,
  "ack_num": 9876543210,
  "window_size": 65535
}
```

#### Connection Format (JSON)
```json
{
  "connection_id": "abc123...",
  "src_ip": "192.168.1.10",
  "src_port": 54321,
  "dst_ip": "93.184.216.34",
  "dst_port": 443,
  "state": "ESTABLISHED",
  "bytes_sent": 123456,
  "bytes_received": 654321,
  "packets_sent": 100,
  "packets_received": 95,
  "rtt_ms": 42.5,
  "retransmissions": 2,
  "window_size": 65535,
  "last_seq": 1234567890,
  "last_ack": 9876543210,
  "first_seen": 1234567890.123,
  "last_seen": 1234567895.456,
  "recent_packets": [...]
}
```

---

## Implementation Details

### Bidirectional Connection Tracking

**Problem**: A TCP connection has two directions (A→B and B→A), but should be treated as one entity.

**Solution**: Normalize connection ID by sorting endpoints:

```python
def get_connection_id(src_ip, src_port, dst_ip, dst_port):
    """Create deterministic ID for bidirectional flow"""
    endpoints = sorted([
        (src_ip, src_port),
        (dst_ip, dst_port)
    ])
    key = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
    return hashlib.md5(key.encode()).hexdigest()
```

### RTT Calculation

**Challenge**: Estimate Round-Trip Time without kernel access.

**Approach 1 - SYN/SYNACK**:
```
Client sends SYN (seq=X) at t1
Server sends SYN-ACK (ack=X+1) at t2
RTT = t2 - t1
```

**Approach 2 - Data/ACK**:
```
Sender transmits data (seq=Y) at t1
Receiver ACKs (ack=Y+len) at t2
RTT = t2 - t1
```

**Implementation**:
```python
# Exponentially Weighted Moving Average
new_rtt = 0.875 * old_rtt + 0.125 * sample_rtt
```

### Retransmission Detection

**Logic**:
```python
seen_seqs = set()
for packet in connection:
    if packet.seq in seen_seqs and packet.payload > 0:
        retransmission_count += 1
    seen_seqs.add(packet.seq)
```

### Thread Safety

**Concurrent Access**:
- Sniffer thread: Writes packets
- HTTP thread: Reads packets

**Protection**:
```python
with self.lock:
    self.packets.append(new_packet)
    self.connections[conn_id] = updated_conn
```

---

## Performance Considerations

### Backend Optimizations

1. **Bounded Packet Buffer**: Keep only last 1000 packets to prevent memory growth
   ```python
   if len(self.packets) > self.max_packets:
       self.packets = self.packets[-self.max_packets:]
   ```

2. **Efficient Connection Lookup**: Use hashed connection_id for O(1) access
   ```python
   self.connections = {}  # Dict, not List
   ```

3. **Minimal Packet Processing**: Extract only necessary fields
   ```python
   # Don't parse full payload, just length
   payload_length = len(packet[TCP].payload)
   ```

### Frontend Optimizations

1. **Controlled Re-renders**: Only update state when data changes
   ```javascript
   if (JSON.stringify(newPackets) !== JSON.stringify(oldPackets)) {
       setPackets(newPackets);
   }
   ```

2. **Virtualized Lists**: For large packet counts, use `react-window` (future)

3. **Debounced Updates**: 1-second polling interval balances freshness and load

### Scalability Limits

| Metric | Limit | Reason |
|--------|-------|--------|
| Packets/sec | ~1000 | Python GIL + JSON serialization |
| Active connections | ~10,000 | Memory-bound (100KB per conn) |
| UI refresh rate | 1 Hz | Browser rendering cost |
| Packet history | 1000 | Bounded deque |

---

## Future Enhancements

### Short-term (v1.1)

1. **WebSocket Streaming**: Replace HTTP polling for real-time push
   ```python
   # Use Flask-SocketIO
   @socketio.on('subscribe')
   def handle_subscribe():
       emit('packet', packet_data)
   ```

2. **Packet Filtering**: UI controls to filter by IP, port, flags
   ```javascript
   <input onChange={e => setFilter({port: e.target.value})} />
   ```

3. **Export to PCAP**: Save captured packets
   ```python
   wrpcap('capture.pcap', packets)
   ```

### Mid-term (v2.0)

1. **eBPF Integration**: Zero-copy packet capture
   ```c
   // BPF program to aggregate stats in kernel
   BPF_HASH(connections, u64, struct tcp_stats);
   ```

2. **gRPC Streaming**: Replace HTTP with gRPC for efficiency
   ```protobuf
   rpc StreamPackets(Empty) returns (stream Packet);
   ```

3. **Historical Analysis**: Store packets in SQLite/TimescaleDB

### Long-term (v3.0)

1. **Distributed Capture**: Multi-host monitoring
2. **ML-based Anomaly Detection**: Detect unusual patterns
3. **Congestion Control Visualization**: Plot cwnd over time

---

## Architecture Decisions

### Why HTTP instead of gRPC?

**Reasons**:
1. **Simplicity**: No proto compilation, easier debugging with curl/browser
2. **Browser compatibility**: No need for gRPC-Web proxy
3. **Development speed**: Faster iteration during prototyping

**Trade-offs**:
- Higher overhead (JSON vs protobuf)
- Polling latency (vs server push)

### Why Scapy instead of libpcap?

**Reasons**:
1. **Python-native**: Easier integration
2. **High-level API**: Don't need to parse raw bytes
3. **Flexibility**: Easy to filter and modify packets

**Trade-offs**:
- Slower than C-based libpcap
- Higher CPU usage

### Why In-memory instead of Database?

**Reasons**:
1. **Low latency**: No disk I/O
2. **Simplicity**: No schema management
3. **Scope**: Focus on live monitoring, not forensics

**Trade-offs**:
- Data lost on restart
- Limited history

---

## Security Considerations

1. **Root Privileges**: Backend requires root for packet capture
   - **Mitigation**: Use capabilities (`CAP_NET_RAW`) instead of full root
   
2. **Local-only API**: No authentication on HTTP endpoint
   - **Mitigation**: Bind to 127.0.0.1 only, use firewall

3. **Packet Capture Privacy**: Can see all traffic on interface
   - **Mitigation**: Document clearly, use on test networks only

---

## Debugging Guide

### Backend Issues

**Enable debug logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Test packet capture**:
```bash
sudo tcpdump -i eth0 -c 10  # Verify interface works
```

**Check API manually**:
```bash
curl http://localhost:50052/api/traffic | jq .
```

### Frontend Issues

**Check browser console** (F12):
```javascript
console.log('Packets:', packets);
console.log('Connections:', connections);
```

**Verify fetch requests**:
```javascript
fetch('http://localhost:50052/api/traffic')
  .then(r => r.json())
  .then(console.log);
```

---

**Maintained by**: Emmanuel Scaria  
**Last Review**: December 14, 2025
