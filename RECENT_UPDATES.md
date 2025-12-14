# Recent Updates - TCP Packet Details

## Changes Made

### Backend Changes (`server_with_http.py`)

1. **Added Sequence and Acknowledgment Number Tracking**
   - Each packet now includes `seq_number`, `ack_number`, and `window` fields
   - These are extracted directly from TCP headers using Scapy

2. **Recent Packets Per Connection**
   - Each connection now tracks the last 5 packets
   - Each packet record includes:
     - Timestamp
     - Sequence number
     - Acknowledgment number  
     - TCP flags
     - Direction (outgoing/incoming)

3. **Enhanced Packet Data**
   - Packet stream now includes SEQ/ACK numbers for analysis
   - Window size is tracked from each packet

### Frontend Changes (`App.js`)

1. **Packet Stream Enhanced**
   - Now displays sequence and acknowledgment numbers for each packet
   - Format: `SEQ:1234567 ACK:7654321`
   - Shown in a smaller font with subtle color (#888)

2. **New "Recent Packets" Section**
   - Added to Connection Details panel
   - Shows last 5 packets for selected connection
   - Displays:
     - Timestamp with milliseconds
     - Direction indicator (→ for outgoing, ← for incoming)
     - Sequence number (formatted with commas)
     - Acknowledgment number (formatted with commas, or '-' if not present)
     - TCP flags (SYN, ACK, PSH, FIN, etc.)
   - Color coding:
     - Outgoing packets: blue (#00aaff)
     - Incoming packets: green (#00ff88)
     - Flags: orange (#ffaa00)

## How to Use

1. **Start the backend:**
   ```bash
   cd backend
   sudo venv/bin/python3 server_with_http.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Generate test traffic:**
   ```bash
   ./test_tcp_connection.sh
   ```

4. **View the data:**
   - Click on any connection in the Active Connections table
   - Scroll down to see the "Recent Packets" section
   - Watch sequence and ACK numbers update in real-time

## Technical Details

The sequence and acknowledgment numbers are crucial for understanding:
- **Reliable delivery**: ACK confirms receipt of data up to that sequence number
- **Flow control**: Sequence numbers ensure in-order delivery
- **Retransmissions**: Same sequence number appearing multiple times indicates retransmission
- **Window management**: Helps analyze TCP window behavior

The direction indicator helps differentiate between:
- **Outgoing (→)**: Packets from the first endpoint (lower IP/port pair)
- **Incoming (←)**: Packets to the first endpoint (responses)

This allows you to observe the TCP handshake (SYN/SYN-ACK/ACK) and data transfer patterns.
