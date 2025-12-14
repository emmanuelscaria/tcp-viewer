# TCP Viewer - API Documentation

**Version**: 1.0  
**Base URL**: `http://localhost:50052`  
**Protocol**: HTTP/1.1 + JSON

---

## Table of Contents

1. [Overview](#overview)
2. [Endpoints](#endpoints)
3. [Data Models](#data-models)
4. [Examples](#examples)
5. [Error Handling](#error-handling)

---

## Overview

TCP Viewer exposes a simple REST API for retrieving real-time packet and connection data. The backend serves JSON responses over HTTP with CORS headers enabled for browser access.

### Base Configuration

```
Host: localhost
Port: 50052
Content-Type: application/json
Access-Control-Allow-Origin: *
```

### Authentication

None required (local-only API)

### Rate Limiting

No rate limiting (recommended client polling: 1 request/second)

---

## Endpoints

### GET /api/traffic

Retrieve current packet stream and active connections.

**Request**
```http
GET /api/traffic HTTP/1.1
Host: localhost:50052
Accept: application/json
```

**Response**
```http
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: *
Content-Length: 1234

{
  "packets": [...],
  "connections": {...}
}
```

**Response Schema**
```json
{
  "packets": [Packet],      // Array of packet objects (max 1000)
  "connections": {          // Dictionary of connection objects
    "connection_id": Connection
  }
}
```

**Typical Response Time**: 5-50ms  
**Payload Size**: 10KB - 500KB (depends on activity)

---

## Data Models

### Packet Object

Represents a single TCP packet captured from the network interface.

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

**Field Descriptions**

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp with microseconds |
| `src_ip` | string | Source IP address (IPv4) |
| `src_port` | integer | Source TCP port (0-65535) |
| `dst_ip` | string | Destination IP address (IPv4) |
| `dst_port` | integer | Destination TCP port (0-65535) |
| `flag_syn` | boolean | SYN flag set (connection initiation) |
| `flag_ack` | boolean | ACK flag set (acknowledgment) |
| `flag_fin` | boolean | FIN flag set (graceful close) |
| `flag_rst` | boolean | RST flag set (connection reset) |
| `flag_psh` | boolean | PSH flag set (push data immediately) |
| `flag_urg` | boolean | URG flag set (urgent data) |
| `payload_length` | integer | TCP payload size in bytes |
| `seq_num` | integer | TCP sequence number |
| `ack_num` | integer | TCP acknowledgment number |
| `window_size` | integer | TCP receive window size |

**Packet Ordering**: Newest first (reverse chronological)

---

### Connection Object

Represents an aggregated bidirectional TCP connection with computed metrics.

```json
{
  "connection_id": "abc123def456...",
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
  "first_seen": 1702560896.123,
  "last_seen": 1702560901.456,
  "recent_packets": [...]
}
```

**Field Descriptions**

| Field | Type | Description |
|-------|------|-------------|
| `connection_id` | string | MD5 hash of normalized 4-tuple |
| `src_ip` | string | Source IP (alphabetically first endpoint) |
| `src_port` | integer | Source port |
| `dst_ip` | string | Destination IP (alphabetically second endpoint) |
| `dst_port` | integer | Destination port |
| `state` | string | TCP state (see States section) |
| `bytes_sent` | integer | Total bytes sent (src → dst) |
| `bytes_received` | integer | Total bytes received (dst → src) |
| `packets_sent` | integer | Total packets sent (src → dst) |
| `packets_received` | integer | Total packets received (dst → src) |
| `rtt_ms` | float | Smoothed round-trip time in milliseconds |
| `retransmissions` | integer | Count of detected retransmitted packets |
| `window_size` | integer | Most recent receive window size |
| `last_seq` | integer | Latest sequence number seen |
| `last_ack` | integer | Latest acknowledgment number seen |
| `first_seen` | float | Unix timestamp of first packet |
| `last_seen` | float | Unix timestamp of most recent packet |
| `recent_packets` | array | Last 5 packets for this connection |

**Connection ID Generation**:
```python
# Deterministic bidirectional ID
endpoints = sorted([(src_ip, src_port), (dst_ip, dst_port)])
key = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
connection_id = hashlib.md5(key.encode()).hexdigest()
```

---

### TCP States

Possible values for `connection.state`:

| State | Hex Code | Description |
|-------|----------|-------------|
| `ESTABLISHED` | 0x01 | Active data transfer |
| `SYN_SENT` | 0x02 | Client waiting for SYN-ACK |
| `SYN_RECV` | 0x03 | Server received SYN |
| `FIN_WAIT1` | 0x04 | Initiating graceful close |
| `FIN_WAIT2` | 0x05 | Waiting for remote FIN |
| `TIME_WAIT` | 0x06 | Waiting before full close |
| `CLOSE` | 0x07 | Connection closed |
| `CLOSE_WAIT` | 0x08 | Remote closed, local pending |
| `LAST_ACK` | 0x09 | Waiting for final ACK |
| `LISTEN` | 0x0A | Passive open (server) |
| `CLOSING` | 0x0B | Simultaneous close |

**Source**: `/proc/net/tcp` kernel interface or inferred from packet flags

---

### Recent Packet Sub-Object

Part of Connection object - last 5 packets for detailed inspection.

```json
{
  "timestamp": "2025-12-14T12:34:56.789012",
  "direction": "sent",
  "flags": "PSH,ACK",
  "seq": 1234567890,
  "ack": 9876543210,
  "len": 1460
}
```

**Fields**:
- `timestamp`: Packet capture time
- `direction`: `"sent"` or `"received"` (relative to src_ip)
- `flags`: Comma-separated TCP flags (e.g., "SYN,ACK")
- `seq`: Sequence number
- `ack`: Acknowledgment number
- `len`: Payload length in bytes

---

## Examples

### Example 1: Fetch All Data

**Request**:
```bash
curl http://localhost:50052/api/traffic
```

**Response** (truncated):
```json
{
  "packets": [
    {
      "timestamp": "2025-12-14T12:34:56.123456",
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
      "payload_length": 156,
      "seq_num": 1234567890,
      "ack_num": 9876543210,
      "window_size": 65535
    }
  ],
  "connections": {
    "abc123...": {
      "connection_id": "abc123...",
      "src_ip": "192.168.1.10",
      "src_port": 54321,
      "dst_ip": "93.184.216.34",
      "dst_port": 443,
      "state": "ESTABLISHED",
      "bytes_sent": 1234,
      "bytes_received": 5678,
      "packets_sent": 10,
      "packets_received": 8,
      "rtt_ms": 15.3,
      "retransmissions": 0,
      "window_size": 65535,
      "last_seq": 1234567890,
      "last_ack": 9876543210,
      "first_seen": 1702560896.123,
      "last_seen": 1702560901.456,
      "recent_packets": []
    }
  }
}
```

### Example 2: Parse with jq

**Get packet count**:
```bash
curl -s http://localhost:50052/api/traffic | jq '.packets | length'
# Output: 245
```

**List connection states**:
```bash
curl -s http://localhost:50052/api/traffic | \
  jq '.connections | to_entries | .[].value.state'
# Output:
# "ESTABLISHED"
# "TIME_WAIT"
# "FIN_WAIT1"
```

**Filter HTTPS connections**:
```bash
curl -s http://localhost:50052/api/traffic | \
  jq '.connections | to_entries | .[].value | select(.dst_port == 443)'
```

### Example 3: Python Client

```python
import requests
import json

# Fetch data
response = requests.get('http://localhost:50052/api/traffic')
data = response.json()

# Print summary
print(f"Total packets: {len(data['packets'])}")
print(f"Active connections: {len(data['connections'])}")

# Analyze connections
for conn_id, conn in data['connections'].items():
    print(f"\nConnection: {conn['src_ip']}:{conn['src_port']} -> {conn['dst_ip']}:{conn['dst_port']}")
    print(f"  State: {conn['state']}")
    print(f"  Sent: {conn['bytes_sent']} bytes in {conn['packets_sent']} packets")
    print(f"  Received: {conn['bytes_received']} bytes in {conn['packets_received']} packets")
    print(f"  RTT: {conn['rtt_ms']:.1f} ms")
```

### Example 4: JavaScript (Frontend)

```javascript
// Fetch with async/await
async function getTraffic() {
  try {
    const response = await fetch('http://localhost:50052/api/traffic');
    const data = await response.json();
    
    console.log('Packets:', data.packets.length);
    console.log('Connections:', Object.keys(data.connections).length);
    
    return data;
  } catch (error) {
    console.error('Failed to fetch traffic:', error);
  }
}

// Use in React component
useEffect(() => {
  const interval = setInterval(async () => {
    const traffic = await getTraffic();
    setPackets(traffic.packets);
    setConnections(Object.values(traffic.connections));
  }, 1000);
  
  return () => clearInterval(interval);
}, []);
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Successful response |
| 500 | Internal Server Error | Backend error (check logs) |

### Error Response Format

```json
{
  "error": "Internal server error",
  "details": "Exception message here"
}
```

### Common Errors

**Backend Not Running**:
```bash
curl http://localhost:50052/api/traffic
# curl: (7) Failed to connect to localhost port 50052: Connection refused
```
**Solution**: Start backend with `sudo venv/bin/python3 server.py`

**CORS Error** (in browser):
```
Access to fetch at 'http://localhost:50052/api/traffic' from origin 'http://localhost:3000' 
has been blocked by CORS policy
```
**Solution**: Backend already sends CORS headers - check if backend is running

**Empty Response**:
```json
{
  "packets": [],
  "connections": {}
}
```
**Causes**:
- No traffic on monitored interface
- Wrong interface selected (e.g., monitoring `eth0` but traffic on `wlan0`)
- Insufficient permissions (not running with sudo)

---

## Performance Notes

### Response Time

- **Typical**: 5-20ms for 100 connections
- **Heavy load**: 50-100ms for 1000+ packets
- **Bottleneck**: JSON serialization of large packet arrays

### Payload Size

- **Minimal** (no traffic): ~50 bytes
- **Light** (10 connections): ~5 KB
- **Medium** (100 connections): ~50 KB  
- **Heavy** (1000 packets + 100 connections): ~500 KB

### Caching

No caching - every request returns fresh data.

**Recommendation**: Implement client-side caching with ETags (future enhancement)

---

## Integration Examples

### Prometheus Metrics Export

```python
# Export connection count metric
import requests
from prometheus_client import Gauge, start_http_server

connection_gauge = Gauge('tcp_connections_total', 'Active TCP connections')

def update_metrics():
    data = requests.get('http://localhost:50052/api/traffic').json()
    connection_gauge.set(len(data['connections']))

start_http_server(8000)  # Expose on :8000/metrics
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "panels": [
      {
        "title": "Active Connections",
        "type": "graph",
        "datasource": "JSON API",
        "targets": [{
          "url": "http://localhost:50052/api/traffic",
          "jsonPath": "$.connections.length"
        }]
      }
    ]
  }
}
```

---

## Future API Enhancements (Planned)

### v1.1 - Filtering

```http
GET /api/traffic?ip=192.168.1.10
GET /api/traffic?port=443
GET /api/traffic?state=ESTABLISHED
```

### v2.0 - WebSocket Streaming

```javascript
const ws = new WebSocket('ws://localhost:50052/stream');
ws.onmessage = (event) => {
  const packet = JSON.parse(event.data);
  console.log('New packet:', packet);
};
```

### v2.0 - Historical Queries

```http
GET /api/traffic/history?start=1702560000&end=1702563600
```

---

**API Version**: 1.0  
**Last Updated**: December 14, 2025  
**Maintainer**: Emmanuel Scaria
