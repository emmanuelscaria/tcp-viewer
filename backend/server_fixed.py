#!/usr/bin/env python3
"""
TCP Viewer - Simplified Backend
Fixed version that properly tracks connections
"""

import socket
import hashlib
import json
from datetime import datetime
from threading import Thread, Lock
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import defaultdict

try:
    from scapy.all import sniff, TCP, IP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False


class TcpMonitor:
    """Simple TCP connection monitor"""
    
    def __init__(self):
        self.packets = []
        self.connections = {}
        self.lock = Lock()
        self.max_packets = 1000
    
    def add_packet_and_update_connection(self, pkt_data, conn_data):
        """Atomically add packet and update connection"""
        with self.lock:
            # Add packet
            self.packets.append(pkt_data)
            if len(self.packets) > self.max_packets:
                self.packets = self.packets[-self.max_packets:]
            
            # Update connection
            conn_id = conn_data['connection_id']
            self.connections[conn_id] = conn_data
    
    def get_data(self):
        """Get current state"""
        with self.lock:
            return {
                'packets': self.packets[-100:],  # Last 100 packets
                'connections': list(self.connections.values())
            }


monitor = TcpMonitor()


def packet_handler(pkt):
    """Handle each captured packet"""
    if not (pkt.haslayer(TCP) and pkt.haslayer(IP)):
        return
    
    try:
        ip = pkt[IP]
        tcp = pkt[TCP]
        
        # Create packet record
        packet_data = {
            'timestamp': datetime.now().isoformat(),
            'src_ip': ip.src,
            'src_port': tcp.sport,
            'dst_ip': ip.dst,
            'dst_port': tcp.dport,
            'flag_syn': bool(tcp.flags.S),
            'flag_ack': bool(tcp.flags.A),
            'flag_fin': bool(tcp.flags.F),
            'flag_rst': bool(tcp.flags.R),
            'flag_psh': bool(tcp.flags.P),
            'flag_urg': bool(tcp.flags.U),
            'payload_length': len(tcp.payload),
            'seq_number': tcp.seq,
            'ack_number': tcp.ack if tcp.flags.A else 0,
            'window': tcp.window,
        }
        
        # Create bidirectional connection ID
        endpoints = tuple(sorted([(ip.src, tcp.sport), (ip.dst, tcp.dport)]))
        conn_str = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
        conn_id = hashlib.md5(conn_str.encode()).hexdigest()[:16]
        
        # Get or create connection
        if conn_id in monitor.connections:
            conn = monitor.connections[conn_id].copy()
        else:
            conn = {
                'connection_id': conn_id,
                'src_ip': endpoints[0][0],
                'src_port': endpoints[0][1],
                'dst_ip': endpoints[1][0],
                'dst_port': endpoints[1][1],
                'state': 'UNKNOWN',
                'bytes_sent': 0,
                'bytes_received': 0,
                'packet_count': 0,
                'created_at': datetime.now().isoformat(),
                'snd_cwnd': 10,
                'snd_ssthresh': 64,
                'snd_wnd': 65535,
                'rcv_wnd': 0,
                'srtt': 0,
                'rto': 200,
                'retransmits': 0
            }
        
        # Update connection stats
        conn['packet_count'] += 1
        conn['rcv_wnd'] = tcp.window
        conn['last_seq'] = tcp.seq
        conn['last_ack'] = tcp.ack if tcp.flags.A else 0
        conn['last_window'] = tcp.window
        conn['last_timestamp'] = packet_data['timestamp']
        conn['timestamp'] = datetime.now().isoformat()
        
        # Determine direction and update bytes
        if ip.src == conn['src_ip'] and tcp.sport == conn['src_port']:
            conn['bytes_sent'] += len(tcp.payload)
        else:
            conn['bytes_received'] += len(tcp.payload)
        
        # Update state based on flags
        if tcp.flags.S and not tcp.flags.A:
            conn['state'] = 'SYN_SENT'
        elif tcp.flags.S and tcp.flags.A:
            conn['state'] = 'SYN_RECEIVED'
        elif tcp.flags.A and conn['state'] in ['SYN_SENT', 'SYN_RECEIVED', 'UNKNOWN']:
            conn['state'] = 'ESTABLISHED'
        
        if tcp.flags.F:
            conn['state'] = 'FIN_WAIT'
        if tcp.flags.R:
            conn['state'] = 'CLOSED'
        
        # Store both packet and connection atomically
        monitor.add_packet_and_update_connection(packet_data, conn)
        
    except Exception as e:
        print(f"❌ Error in packet_handler: {e}")
        import traceback
        traceback.print_exc()


def start_capture(interface='eth0'):
    """Start packet capture in background"""
    if not SCAPY_AVAILABLE:
        print("❌ Scapy not available")
        return
    
    def capture_loop():
        print(f"🔍 Capturing on {interface}...")
        try:
            sniff(iface=interface, prn=packet_handler, store=False)
        except Exception as e:
            print(f"❌ Capture error: {e}")
    
    Thread(target=capture_loop, daemon=True).start()


class APIHandler(BaseHTTPRequestHandler):
    """HTTP API handler"""
    
    def do_GET(self):
        if self.path == '/api/traffic':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = monitor.get_data()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == '/api/stats':
            # Debug endpoint
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            stats = {
                'total_packets': len(monitor.packets),
                'total_connections': len(monitor.connections),
                'connection_ids': list(monitor.connections.keys())[:10]
            }
            self.wfile.write(json.dumps(stats).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress logging


def main():
    print("=" * 50)
    print("TCP Viewer - Fixed Backend")
    print("=" * 50)
    
    # Start HTTP API
    server = HTTPServer(('0.0.0.0', 50052), APIHandler)
    Thread(target=server.serve_forever, daemon=True).start()
    print(f"✅ HTTP API on port 50052")
    print(f"   http://localhost:50052/api/traffic")
    print(f"   http://localhost:50052/api/stats (debug)")
    
    # Start packet capture
    start_capture('eth0')
    
    print("\nPress Ctrl+C to stop\n")
    
    try:
        import signal
        signal.pause()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == '__main__':
    import os
    if os.geteuid() != 0:
        print("⚠️  Warning: Not running as root")
        print("   Run: sudo venv/bin/python3 server_fixed.py\n")
    main()
