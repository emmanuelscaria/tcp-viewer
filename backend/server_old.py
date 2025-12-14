#!/usr/bin/env python3
"""
TCP Viewer - Backend HTTP REST API Server
Provides HTTP REST API for packet capture and TCP connection monitoring
No gRPC - Pure HTTP/JSON communication
"""

import socket
import hashlib
import json
from datetime import datetime
from threading import Thread, Lock
from http.server import HTTPServer, BaseHTTPRequestHandler
from tcp_introspector import get_tcp_info_via_ss
from tcp_packet_analyzer import TcpPacketAnalyzer

try:
    from scapy.all import sniff, TCP, IP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Warning: Scapy not available. Install with: pip install scapy")


# Global data storage for HTTP API
class DataStore:
    """In-memory storage for packets and connections"""
    def __init__(self, max_packets=1000):
        self.packets = []
        self.connections = {}
        self.max_packets = max_packets
        self.lock = Lock()
    
    def add_packet(self, packet_dict):
        with self.lock:
            self.packets.append(packet_dict)
            if len(self.packets) > self.max_packets:
                self.packets = self.packets[-self.max_packets:]
    
    def update_connection(self, conn_id, conn_dict):
        with self.lock:
            self.connections[conn_id] = conn_dict
    
    def get_data(self):
        with self.lock:
            return {
                'packets': self.packets.copy(),
                'connections': list(self.connections.values())
            }


data_store = DataStore()
_active_connections = {}


def start_packet_capture(interface='eth0'):
    """Start background packet capture that feeds the HTTP endpoint"""
    if not SCAPY_AVAILABLE:
        print("❌ Scapy not available - packet capture disabled")
        return
    
    print(f"🔍 Starting packet capture on interface: {interface}")
    
    # Initialize packet analyzer
    analyzer = TcpPacketAnalyzer()
    
    def packet_handler(pkt):
        # Filter TCP packets in Python instead of using BPF filter
        if not (pkt.haslayer(TCP) and pkt.haslayer(IP)):
            return
            
        try:
            ip_layer = pkt[IP]
            tcp_layer = pkt[TCP]
            
            # Store packet in HTTP bridge with TCP header details
            packet_dict = {
                'timestamp': datetime.now().isoformat(),
                'src_ip': ip_layer.src,
                'src_port': tcp_layer.sport,
                'dst_ip': ip_layer.dst,
                'dst_port': tcp_layer.dport,
                'flag_syn': bool(tcp_layer.flags.S),
                'flag_ack': bool(tcp_layer.flags.A),
                'flag_fin': bool(tcp_layer.flags.F),
                'flag_rst': bool(tcp_layer.flags.R),
                'flag_psh': bool(tcp_layer.flags.P),
                'flag_urg': bool(tcp_layer.flags.U),
                'payload_length': len(tcp_layer.payload),
                'seq_number': tcp_layer.seq,
                'ack_number': tcp_layer.ack if tcp_layer.flags.A else 0,
                'window': tcp_layer.window,
            }
            data_store.add_packet(packet_dict)
            
            # Update connections - use bidirectional ID
            endpoints = sorted([
                (ip_layer.src, tcp_layer.sport),
                (ip_layer.dst, tcp_layer.dport)
            ])
            conn_str = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
            conn_id = hashlib.md5(conn_str.encode()).hexdigest()[:16]
            
            # DEBUG: First time we see this connection
            is_new = conn_id not in _active_connections
            
            if is_new:
                _active_connections[conn_id] = {
                    'connection_id': conn_id,
                    'src_ip': endpoints[0][0],
                    'src_port': endpoints[0][1],
                    'dst_ip': endpoints[1][0],
                    'dst_port': endpoints[1][1],
                    'state': 'UNKNOWN',
                    'bytes_sent': 0,
                    'bytes_received': 0,
                    'created_at': datetime.now().isoformat(),
                    'packets': []
                }
                print(f"🆕 New connection: {conn_str} (ID: {conn_id})")
            
            conn = _active_connections[conn_id]
            
            # Determine packet direction and update bytes
            if ip_layer.src == conn['src_ip'] and tcp_layer.sport == conn['src_port']:
                conn['bytes_sent'] += len(tcp_layer.payload)
                direction = 'sent'
            else:
                conn['bytes_received'] += len(tcp_layer.payload)
                direction = 'received'
            
            # Update state based on TCP flags
            if tcp_layer.flags.S and not tcp_layer.flags.A:
                conn['state'] = 'SYN_SENT'
            elif tcp_layer.flags.S and tcp_layer.flags.A:
                conn['state'] = 'SYN_RECEIVED'
            elif tcp_layer.flags.A:
                if conn['state'] in ['SYN_SENT', 'SYN_RECEIVED', 'UNKNOWN']:
                    conn['state'] = 'ESTABLISHED'
            if tcp_layer.flags.F:
                conn['state'] = 'FIN_WAIT'
            if tcp_layer.flags.R:
                conn['state'] = 'CLOSED'
            
            # Track recent packets for RTT calculation
            conn['packets'].append({
                'timestamp': datetime.now().isoformat(),
                'seq': tcp_layer.seq,
                'ack': tcp_layer.ack if tcp_layer.flags.A else 0,
                'window': tcp_layer.window,
                'direction': direction
            })
            
            # Keep only last 100 packets per connection
            if len(conn['packets']) > 100:
                conn['packets'] = conn['packets'][-100:]
            
            # Process packet for RTT estimation
            try:
                analyzer.process_packet(
                    src_ip=ip_layer.src,
                    src_port=tcp_layer.sport,
                    dst_ip=ip_layer.dst,
                    dst_port=tcp_layer.dport,
                    seq=tcp_layer.seq,
                    ack=tcp_layer.ack if tcp_layer.flags.A else 0,
                    timestamp=datetime.now().timestamp(),
                    is_syn=bool(tcp_layer.flags.S),
                    is_ack=bool(tcp_layer.flags.A)
                )
            except Exception as e:
                print(f"⚠️  RTT analyzer error: {e}")
            
            try:
                stats = analyzer.get_connection_stats(
                    conn['src_ip'], conn['src_port'],
                    conn['dst_ip'], conn['dst_port']
                )
            except Exception as e:
                print(f"⚠️  Get stats error: {e}")
                stats = {}
            
            # Get kernel stats via ss
            try:
                kernel_stats = get_tcp_info_via_ss(
                    conn['src_ip'], conn['src_port'],
                    conn['dst_ip'], conn['dst_port']
                )
            except Exception as e:
                print(f"⚠️  Kernel stats error: {e}")
                kernel_stats = None
            
            # Merge all stats
            conn['snd_cwnd'] = kernel_stats.get('snd_cwnd', 10) if kernel_stats else 10
            conn['snd_ssthresh'] = kernel_stats.get('snd_ssthresh', 64) if kernel_stats else 64
            conn['snd_wnd'] = kernel_stats.get('snd_wnd', 65535) if kernel_stats else 65535
            conn['rcv_wnd'] = tcp_layer.window  # From packet
            conn['srtt'] = stats.get('avg_rtt', kernel_stats.get('srtt', 0)) if kernel_stats else stats.get('avg_rtt', 0)
            conn['rto'] = kernel_stats.get('rto', 200) if kernel_stats else 200
            conn['retransmits'] = kernel_stats.get('retransmits', 0) if kernel_stats else 0
            
            # Add recent packet details
            if conn['packets']:
                latest = conn['packets'][-1]
                conn['last_seq'] = latest['seq']
                conn['last_ack'] = latest['ack']
                conn['last_window'] = latest['window']
                conn['last_timestamp'] = latest['timestamp']
            
            conn['timestamp'] = datetime.now().isoformat()
            
            # Update data store - THIS IS CRITICAL!
            data_store.update_connection(conn_id, conn)
            
            # Debug: Verify it was added
            if is_new:
                stored_count = len(data_store.connections)
                print(f"   ✅ Stored in data_store (total connections: {stored_count})")
            
        except Exception as e:
            print(f"❌ Error processing packet: {e}")
            import traceback
            traceback.print_exc()
    
    def sniff_packets():
        try:
            print(f"\nNote: Packet capture requires root/sudo privileges")
            print("✅ Capturing all packets (filtering TCP in Python)")
            print()
            # Remove BPF filter - filter in Python instead
            sniff(
                iface=interface,
                prn=packet_handler,
                store=False
            )
        except PermissionError:
            print("❌ Permission denied. Run with sudo/root privileges")
        except Exception as e:
            print(f"Sniffing error: {e}")
            import traceback
            traceback.print_exc()
    
    # Start sniffing in background thread
    sniffer_thread = Thread(target=sniff_packets, daemon=True)
    sniffer_thread.start()


class HTTPBridge(BaseHTTPRequestHandler):
    """Simple HTTP server to expose packet/connection data as JSON"""
    
    def do_GET(self):
        if self.path == '/api/traffic':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            data = data_store.get_data()
            self.wfile.write(json.dumps(data).encode())
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
        # Suppress HTTP request logging
        pass


def serve(http_port=50052):
    """Start HTTP server"""
    
    print("=========================================")
    print("TCP Viewer - Backend Server")
    print("=========================================\n")
    
    # Start HTTP server
    http_server = HTTPServer(('0.0.0.0', http_port), HTTPBridge)
    http_thread = Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    
    print(f"✅ HTTP REST API started on port {http_port}")
    print(f"   Access: http://localhost:{http_port}/api/traffic")
    print()
    
    # Start background packet capture on eth0
    start_packet_capture(interface='eth0')
    
    print("Press Ctrl+C to stop")
    print()
    
    try:
        import signal
        signal.pause()  # Wait forever
    except KeyboardInterrupt:
        print("\nShutting down server...")
        http_server.shutdown()


if __name__ == '__main__':
    import sys
    import os
    
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Packet capture may fail.")
        print("Run with: sudo venv/bin/python3 server.py")
        print()
    
    serve()
