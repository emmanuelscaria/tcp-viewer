# Real Kernel TCP Metrics Integration

TCP Viewer now reads **real TCP control block data** from the Linux kernel!

## What Changed

**Before:** Placeholder values (cwnd=10, srtt=1000µs for everything)

**After:** Real kernel values from actual TCP connections:
- **snd_cwnd**: Real congestion window (varies per connection)
- **snd_ssthresh**: Real slow-start threshold
- **srtt**: Real smoothed round-trip time (in microseconds)
- **rto**: Real retransmission timeout (in milliseconds)
- **snd_wnd**: Real send window size

## How It Works

TCP Viewer uses two data sources:

### 1. /proc/net/tcp
Basic connection information:
- Source/Destination IP:Port
- TCP State (ESTABLISHED, CLOSE_WAIT, etc.)
- TX/RX Queue sizes

### 2. ss (socket statistics) command
Detailed TCP metrics via `ss -tin`:
```bash
ss -tin '( sport = :443 and dport = :54321 )'
```

Output example:
```
ESTAB  0  0  192.168.1.1:443  192.168.1.2:54321
       cubic wscale:7,7 rto:204 rtt:0.5/0.25 cwnd:10 ssthresh:7
```

Parsed metrics:
- **cwnd**: Congestion window in segments
- **ssthresh**: Slow-start threshold
- **rtt**: Round-trip time (avg/variance)
- **rto**: Retransmission timeout

## Real-World Examples

### Local Connection (Loopback)
```json
{
  "connection_id": "bbe9adc1d949cad1",
  "src_ip": "127.0.0.1",
  "src_port": 47862,
  "dst_ip": "127.0.0.1",
  "dst_port": 3000,
  "state": "ESTABLISHED",
  "snd_cwnd": 10,
  "snd_ssthresh": 65483,
  "srtt": 847,     // 0.847ms RTT (very fast - localhost)
  "rto": 204
}
```

### GitHub Connection (Internet)
```json
{
  "connection_id": "ba752eecd71c8f76",
  "src_ip": "172.21.82.14",
  "src_port": 39628,
  "dst_ip": "140.82.114.21",
  "dst_port": 443,
  "state": "ESTABLISHED",
  "snd_cwnd": 317,      // Large window - high bandwidth
  "snd_ssthresh": 89667,
  "srtt": 250355,       // 250ms RTT (internet latency)
  "rto": 472
}
```

Notice:
- **Localhost**: cwnd=10, RTT<1ms (fast local connection)
- **GitHub**: cwnd=317, RTT=250ms (slow internet connection, large window compensates)

## TCP States Tracked

From Linux kernel `include/net/tcp_states.h`:
- **ESTABLISHED**: Active connection
- **SYN_SENT**: Initial SYN sent
- **SYN_RECV**: SYN received, sent SYN-ACK
- **FIN_WAIT1/2**: Connection closing
- **TIME_WAIT**: 2MSL wait after close
- **CLOSE**: Connection closed
- **CLOSE_WAIT**: Remote closed, local still open
- **LAST_ACK**: Final ACK wait
- **LISTEN**: Server listening
- **CLOSING**: Simultaneous close

## Performance Considerations

**ss command overhead:**
- Called once per connection per packet
- ~1-2ms overhead per call
- Acceptable for moderate traffic (<100 connections)

**Optimization for high traffic:**
- Cache ss results for 100ms
- Only update on state changes
- Use connection pooling

## Testing

Generate traffic and watch real metrics:
```bash
# Start backend
cd ~/tcp-viewer/backend
sudo venv/bin/python3 server_with_http.py

# Generate different traffic types
curl https://google.com           # See high latency, varying cwnd
curl http://localhost:3000         # See low latency, stable cwnd
wget https://kernel.org/linux.tar.gz  # See cwnd growth over time

# Check real metrics
curl http://localhost:50052/api/traffic | jq '.connections[] | {
  conn: "\(.src_ip):\(.src_port) ↔ \(.dst_ip):\(.dst_port)",
  state: .state,
  cwnd: .snd_cwnd,
  rtt_us: .srtt,
  rtt_ms: (.srtt / 1000)
}'
```

## Next Steps (Future Enhancements)

**Phase 3 - eBPF Integration:**
- Use BCC/libbpf to attach to kernel TCP functions
- Zero-copy access to TCP control block
- Real-time updates without ss overhead
- Access to more internal metrics:
  - Retransmission count
  - Out-of-order segments
  - SACK blocks
  - Fast retransmit triggers

**Example eBPF program:**
```python
from bcc import BPF

bpf_code = """
#include <net/sock.h>

struct tcp_event {
    u32 saddr;
    u32 daddr;
    u16 sport;
    u16 dport;
    u32 snd_cwnd;
    u32 srtt_us;
};

BPF_PERF_OUTPUT(events);

int trace_tcp_sendmsg(struct pt_regs *ctx, struct sock *sk) {
    struct tcp_sock *tp = tcp_sk(sk);
    struct tcp_event evt = {};
    
    evt.snd_cwnd = tp->snd_cwnd;
    evt.srtt_us = tp->srtt_us >> 3;  // Convert to microseconds
    
    events.perf_submit(ctx, &evt, sizeof(evt));
    return 0;
}
"""
```

## References

- Linux kernel source: `net/ipv4/tcp.c`
- `ss` command source: `iproute2/misc/ss.c`
- `/proc/net/tcp` format: `Documentation/networking/proc_net_tcp.txt`
- TCP states: `include/net/tcp_states.h`
