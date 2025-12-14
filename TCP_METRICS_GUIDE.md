# TCP Metrics Quick Reference Guide

Visual guide to understanding the TCP Control Block metrics displayed in TCP Viewer.

---

## 📊 Metrics Categories

### 1. Congestion Control

**Purpose:** Prevent network congestion by controlling send rate

#### Congestion Window (cwnd)
- **What:** Number of TCP segments that can be in-flight (unacknowledged)
- **Units:** Segments (typically 1460 bytes each)
- **Range:** 1 to ~65535
- **Good Value:** Varies by network
  - Local: 10-50
  - Internet: 100-500+
- **How to Read:**
  - Small cwnd = Limited throughput
  - Large cwnd = High throughput capacity
  - Growing cwnd = Network has capacity
  - Shrinking cwnd = Congestion detected

#### Slow Start Threshold (ssthresh)
- **What:** Boundary between slow start and congestion avoidance
- **Units:** Segments
- **Range:** Typically 60000-100000
- **Behavior:**
  - cwnd < ssthresh → **Slow Start** (exponential growth)
  - cwnd ≥ ssthresh → **Congestion Avoidance** (linear growth)

#### Window Utilization
- **Formula:** (cwnd / ssthresh) × 100%
- **Interpretation:**
  - < 1% = In slow start phase
  - > 50% = Approaching congestion
  - > 100% = In congestion avoidance

---

### 2. Flow Control

**Purpose:** Prevent sender from overwhelming receiver's buffer

#### Send Window (snd_wnd)
- **What:** Receiver's advertised available buffer space
- **Units:** Bytes
- **Typical:** 65535 (64KB) without window scaling
- **Meaning:** How much data receiver can accept

#### Receive Window (rcv_wnd)
- **What:** Local receive buffer space
- **Units:** Bytes
- **Impact:** Limits incoming data rate

#### Effective Window
- **Formula:** min(cwnd × MSS, snd_wnd)
- **What:** Actual sending capacity
- **Why:** Limited by both congestion control AND flow control
- **Example:**
  ```
  cwnd = 100, MSS = 1460, snd_wnd = 65535
  Effective = min(100 × 1460, 65535) = min(146000, 65535) = 65535
  → Flow control is the bottleneck
  ```

---

### 3. Round-Trip Time & Retransmission

#### Smoothed RTT (srtt)
- **What:** Exponentially weighted moving average of round-trip time
- **Units:** Microseconds (µs)
- **Formula:** SRTT = (7/8) × old_SRTT + (1/8) × new_RTT_sample
- **Categories:**
  - 🟢 **Excellent:** < 1,000 µs (< 1ms) - Localhost
  - 🟢 **Good:** 1,000 - 50,000 µs (1-50ms) - LAN/CDN
  - 🟡 **Fair:** 50,000 - 150,000 µs (50-150ms) - Internet
  - 🔴 **High:** > 150,000 µs (> 150ms) - Satellite/Congested

#### Retransmission Timeout (RTO)
- **What:** Time to wait before retransmitting unacked data
- **Units:** Milliseconds (ms)
- **Formula:** RTO = SRTT + 4 × RTTVAR
- **Typical:** 200-1000ms
- **Impact:** Higher RTO = longer wait on packet loss

---

### 4. Performance Insights

#### Bandwidth-Delay Product (BDP)
- **Formula:** cwnd × MSS
- **What:** Optimal buffer size for this connection
- **Example:**
  ```
  cwnd = 317, MSS = 1460
  BDP = 317 × 1460 = 462,820 bytes ≈ 452 KB
  ```

#### Theoretical Max Throughput
- **Formula:** (cwnd × MSS × 8) / RTT (in seconds)
- **Units:** Bits per second (bps)
- **Example:**
  ```
  cwnd = 317, MSS = 1460, RTT = 250ms
  Throughput = (317 × 1460 × 8) / 0.25
             = 3,702,560 / 0.25
             = 14.8 Mbps
  ```
- **Reality Check:** Actual throughput is typically 60-80% of theoretical

---

## 🎯 Real-World Examples

### Example 1: Localhost Connection
```json
{
  "src": "127.0.0.1:47862",
  "dst": "127.0.0.1:3000",
  "state": "ESTABLISHED",
  
  "snd_cwnd": 10,           ← Small window (low latency, don't need big buffer)
  "snd_ssthresh": 65483,    ← Still in slow start
  "snd_wnd": 65535,
  
  "srtt": 847,              ← 0.847ms RTT (🟢 Excellent)
  "rto": 204                ← 204ms RTO
}

Analysis:
✅ Low latency → Small cwnd is fine
✅ In slow start (cwnd << ssthresh)
✅ Not bottlenecked (cwnd < snd_wnd)
```

### Example 2: Internet Connection (GitHub)
```json
{
  "src": "172.21.82.14:39628",
  "dst": "140.82.114.21:443",
  "state": "ESTABLISHED",
  
  "snd_cwnd": 317,          ← Large window (compensates for latency)
  "snd_ssthresh": 89667,    ← Still growing
  "snd_wnd": 65535,
  
  "srtt": 250355,           ← 250ms RTT (🔴 High)
  "rto": 472                ← 472ms RTO
}

Analysis:
⚠️  High latency → Needs large cwnd for throughput
✅ In slow start (cwnd < ssthresh)
❌ Flow control limit reached! (cwnd × MSS > snd_wnd)
💡 Max throughput ≈ 15 Mbps (limited by window scaling)
```

### Example 3: Congestion Event
```json
{
  "snd_cwnd": 45000,        ← Was high
  "snd_ssthresh": 45000,    ← Now equal!
  
  "srtt": 85000,            ← RTT increased
  "rto": 340
}

Analysis:
🚨 Congestion detected!
   - ssthresh dropped to current cwnd
   - Switched to congestion avoidance
   - RTT increased (queuing delay)
```

---

## 🔍 Troubleshooting with TCP Metrics

### Problem: Low Throughput on Fast Network

**Check:**
1. **Small cwnd?** → Congestion control limiting
   - Solution: Tune TCP congestion control algorithm
2. **Small snd_wnd?** → Receiver buffer limited
   - Solution: Enable TCP window scaling
3. **High RTT?** → Geography or routing
   - Solution: Use CDN or optimize routes

### Problem: High Latency

**Check:**
1. **srtt > 100ms?** → Long distance or congestion
2. **RTO very high?** → Network instability
3. **cwnd constantly changing?** → Packet loss/reordering

### Problem: Connection Stuck

**Check:**
1. **State = CLOSE_WAIT?** → Application didn't close socket
2. **State = FIN_WAIT2?** → Remote didn't send FIN
3. **bytes_sent = 0?** → No data transmitted

---

## 📚 TCP State Machine

```
CLOSED
  ↓ (active open)
SYN_SENT
  ↓ (rcv SYN+ACK)
ESTABLISHED ←→ Normal data transfer
  ↓ (close)
FIN_WAIT1
  ↓ (rcv ACK)
FIN_WAIT2
  ↓ (rcv FIN)
TIME_WAIT (2MSL timer)
  ↓
CLOSED
```

**Passive Close:**
```
ESTABLISHED
  ↓ (rcv FIN)
CLOSE_WAIT (app must close)
  ↓ (close)
LAST_ACK
  ↓ (rcv ACK)
CLOSED
```

---

## 🧮 Useful Calculations

### Maximum Possible Throughput
```
Throughput = Window / RTT

Example:
Window = 65535 bytes
RTT = 100ms = 0.1s

Throughput = 65535 / 0.1 = 655,350 bytes/s ≈ 5.2 Mbps
```

### Required Window for Target Throughput
```
Window = Throughput × RTT

Example:
Target = 100 Mbps = 12,500,000 bytes/s
RTT = 50ms = 0.05s

Window = 12,500,000 × 0.05 = 625,000 bytes ≈ 610 KB
```

### Packet Loss Impact
```
Throughput ≈ (MSS / RTT) × (1 / √packet_loss)

Example:
MSS = 1460 bytes
RTT = 100ms = 0.1s
Packet loss = 1% = 0.01

Throughput ≈ (1460 / 0.1) × (1 / √0.01)
          ≈ 14,600 × 10
          ≈ 146,000 bytes/s ≈ 1.16 Mbps

1% loss → 86% throughput reduction!
```

---

## 🎓 Further Reading

- **RFC 793** - TCP Specification
- **RFC 2581** - TCP Congestion Control
- **RFC 6298** - TCP Retransmission Timer
- **RFC 7323** - TCP Window Scaling
- Linux kernel: `net/ipv4/tcp.c`, `tcp_input.c`, `tcp_output.c`

---

## 🔧 Advanced: eBPF Next Steps

Current implementation uses `ss` command. Future eBPF version will:

✅ Zero overhead (no subprocess calls)
✅ More metrics: retransmit count, SACK blocks, etc.
✅ Real-time updates (attach to kernel functions)
✅ Historical tracking (trace congestion events)

See `KERNEL_METRICS.md` for eBPF integration plan.
