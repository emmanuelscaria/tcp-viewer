#!/usr/bin/env python3
"""
TCP Viewer - Backend with HTTP Bridge
This version adds a simple HTTP endpoint so the browser can fetch data
without needing Envoy proxy
"""

import socket
import struct
import time
import hashlib
import json
from concurrent import futures
from datetime import datetime
from threading import Thread, Lock
from http.server import HTTPServer, BaseHTTPRequestHandler
import grpc

import tcp_monitor_pb2
import tcp_monitor_pb2_grpc

try:
    from scapy.all import sniff, TCP, IP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Warning: Scapy not available. Install with: pip install scapy")


# Shared data store
class DataStore:
    def __init__(self):
        self.packets = []
        self.connections = {}
        self.lock = Lock()
        self.max_packets = 100
    
    def add_packet(self, packet_dict):
        with self.lock:
            self.packets.insert(0, packet_dict)
            if len(self.packets) > self.max_packets:
                self.packets = self.packets[:self.max_packets]
    
    def update_connection(self, conn_id, conn_dict):
        with self.lock:
            self.connections[conn_id] = conn_dict
    
    def get_data(self):
        with self.lock:
            return {
                'packets': self.packets[:50],  # Last 50 packets
                'connections': list(self.connections.values())
            }


data_store = DataStore()


class HTTPBridge(BaseHTTPRequestHandler):
    """Simple HTTP endpoint to serve data to browser"""
    
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
    
    def log_message(self, format, *args):
        pass  # Suppress HTTP logs


class TcpMonitorService(tcp_monitor_pb2_grpc.TcpMonitorServicer):
    """gRPC service implementation for TCP monitoring"""
    
    def __init__(self):
        self.active_connections = {}
        self.packet_buffer = []
        
    def StreamTraffic(self, request, context):
        interface = request.interface_name or None
        print(f"Starting packet capture on interface: {interface or 'all'}")
        
        if not SCAPY_AVAILABLE:
            yield tcp_monitor_pb2.TcpEvent(
                packet=tcp_monitor_pb2.PacketInfo(
                    timestamp=datetime.now().isoformat(),
                    src_ip="ERROR",
                    dst_ip="Scapy not installed",
                )
            )
            return
            
        def packet_handler(pkt):
            if pkt.haslayer(TCP) and pkt.haslayer(IP):
                try:
                    ip_layer = pkt[IP]
                    tcp_layer = pkt[TCP]
                    
                    packet_info = tcp_monitor_pb2.PacketInfo(
                        timestamp=datetime.now().isoformat(),
                        src_ip=ip_layer.src,
                        src_port=tcp_layer.sport,
                        dst_ip=ip_layer.dst,
                        dst_port=tcp_layer.dport,
                        flag_syn=bool(tcp_layer.flags.S),
                        flag_ack=bool(tcp_layer.flags.A),
                        flag_fin=bool(tcp_layer.flags.F),
                        flag_rst=bool(tcp_layer.flags.R),
                        flag_psh=bool(tcp_layer.flags.P),
                        flag_urg=bool(tcp_layer.flags.U),
                        payload_length=len(tcp_layer.payload),
                        seq_number=tcp_layer.seq,
                        ack_number=tcp_layer.ack,
                    )
                    
                    # Also store in HTTP bridge
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
                    }
                    data_store.add_packet(packet_dict)
                    
                    conn_id = self._get_connection_id(
                        ip_layer.src, tcp_layer.sport,
                        ip_layer.dst, tcp_layer.dport
                    )
                    
                    self._update_connection(conn_id, ip_layer, tcp_layer)
                    self.packet_buffer.append(packet_info)
                    
                except Exception as e:
                    print(f"Error processing packet: {e}")
        
        import threading
        
        def sniff_packets():
            try:
                sniff(
                    iface=interface,
                    prn=packet_handler,
                    filter="tcp",
                    store=False,
                    stop_filter=lambda x: not context.is_active()
                )
            except PermissionError:
                print("ERROR: Permission denied. Run with sudo/root privileges")
            except Exception as e:
                print(f"Sniffing error: {e}")
        
        sniffer_thread = threading.Thread(target=sniff_packets, daemon=True)
        sniffer_thread.start()
        
        last_stats_time = time.time()
        
        while context.is_active():
            try:
                while self.packet_buffer:
                    packet = self.packet_buffer.pop(0)
                    yield tcp_monitor_pb2.TcpEvent(packet=packet)
                
                current_time = time.time()
                if current_time - last_stats_time >= 1.0:
                    for conn_id, conn_data in list(self.active_connections.items()):
                        stats = self._get_connection_stats(conn_id, conn_data)
                        yield tcp_monitor_pb2.TcpEvent(stats=stats)
                        
                        # Also update HTTP bridge
                        conn_dict = {
                            'connection_id': conn_id,
                            'src_ip': conn_data['src_ip'],
                            'src_port': conn_data['src_port'],
                            'dst_ip': conn_data['dst_ip'],
                            'dst_port': conn_data['dst_port'],
                            'state': conn_data['state'],
                            'bytes_sent': conn_data['bytes_sent'],
                            'bytes_received': conn_data['bytes_received'],
                            'snd_cwnd': 10,
                            'srtt': 1000,
                            'timestamp': datetime.now().isoformat(),
                        }
                        data_store.update_connection(conn_id, conn_dict)
                    
                    last_stats_time = current_time
                
                time.sleep(0.033)
                
            except Exception as e:
                print(f"Streaming error: {e}")
                break
    
    def _get_connection_id(self, src_ip, src_port, dst_ip, dst_port):
        conn_str = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
        return hashlib.md5(conn_str.encode()).hexdigest()[:16]
    
    def _update_connection(self, conn_id, ip_layer, tcp_layer):
        if conn_id not in self.active_connections:
            self.active_connections[conn_id] = {
                'src_ip': ip_layer.src,
                'src_port': tcp_layer.sport,
                'dst_ip': ip_layer.dst,
                'dst_port': tcp_layer.dport,
                'state': 'UNKNOWN',
                'bytes_sent': 0,
                'bytes_received': 0,
                'created_at': time.time(),
            }
        
        conn = self.active_connections[conn_id]
        
        if tcp_layer.flags.S and not tcp_layer.flags.A:
            conn['state'] = 'SYN_SENT'
        elif tcp_layer.flags.S and tcp_layer.flags.A:
            conn['state'] = 'SYN_RECEIVED'
        elif tcp_layer.flags.A:
            conn['state'] = 'ESTABLISHED'
        elif tcp_layer.flags.F:
            conn['state'] = 'FIN_WAIT'
        elif tcp_layer.flags.R:
            conn['state'] = 'CLOSED'
        
        conn['bytes_sent'] += len(tcp_layer.payload)
        conn['last_seen'] = time.time()
    
    def _get_connection_stats(self, conn_id, conn_data):
        return tcp_monitor_pb2.ConnectionStats(
            connection_id=conn_id,
            src_ip=conn_data['src_ip'],
            src_port=conn_data['src_port'],
            dst_ip=conn_data['dst_ip'],
            dst_port=conn_data['dst_port'],
            state=conn_data['state'],
            snd_cwnd=10,
            snd_ssthresh=64,
            snd_wnd=65535,
            rcv_wnd=65535,
            srtt=1000,
            rto=200,
            bytes_sent=conn_data['bytes_sent'],
            bytes_received=conn_data['bytes_received'],
            timestamp=datetime.now().isoformat(),
        )


def start_packet_capture(interface=None):
    """Start background packet capture that feeds the HTTP endpoint"""
    if not SCAPY_AVAILABLE:
        print("❌ Scapy not available - packet capture disabled")
        return
    
    print(f"🔍 Starting packet capture on interface: {interface or 'all'}")
    
    def packet_handler(pkt):
        if pkt.haslayer(TCP) and pkt.haslayer(IP):
            try:
                ip_layer = pkt[IP]
                tcp_layer = pkt[TCP]
                
                # Store packet in HTTP bridge
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
                }
                data_store.add_packet(packet_dict)
                
                # Update connections
                conn_id = hashlib.md5(f"{ip_layer.src}:{tcp_layer.sport}-{ip_layer.dst}:{tcp_layer.dport}".encode()).hexdigest()[:16]
                
                if conn_id not in _active_connections:
                    _active_connections[conn_id] = {
                        'connection_id': conn_id,
                        'src_ip': ip_layer.src,
                        'src_port': tcp_layer.sport,
                        'dst_ip': ip_layer.dst,
                        'dst_port': tcp_layer.dport,
                        'state': 'UNKNOWN',
                        'bytes_sent': 0,
                        'bytes_received': 0,
                    }
                
                conn = _active_connections[conn_id]
                
                # Update state based on flags
                if tcp_layer.flags.S and not tcp_layer.flags.A:
                    conn['state'] = 'SYN_SENT'
                elif tcp_layer.flags.S and tcp_layer.flags.A:
                    conn['state'] = 'SYN_RECEIVED'
                elif tcp_layer.flags.A:
                    conn['state'] = 'ESTABLISHED'
                elif tcp_layer.flags.F:
                    conn['state'] = 'FIN_WAIT'
                elif tcp_layer.flags.R:
                    conn['state'] = 'CLOSED'
                
                conn['bytes_sent'] += len(tcp_layer.payload)
                conn['timestamp'] = datetime.now().isoformat()
                
                data_store.update_connection(conn_id, conn)
                
            except Exception as e:
                print(f"Error processing packet: {e}")
    
    def sniff_packets():
        try:
            sniff(
                iface=interface,
                prn=packet_handler,
                filter="tcp",
                store=False,
            )
        except PermissionError:
            print("❌ Permission denied. Run with sudo/root privileges")
        except Exception as e:
            print(f"Sniffing error: {e}")
    
    # Start sniffing in background thread
    sniffer_thread = Thread(target=sniff_packets, daemon=True)
    sniffer_thread.start()


_active_connections = {}


def serve(grpc_port=50051, http_port=50052):
    """Start both gRPC and HTTP servers"""
    
    # Start gRPC server
    grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tcp_monitor_pb2_grpc.add_TcpMonitorServicer_to_server(
        TcpMonitorService(), grpc_server
    )
    grpc_server.add_insecure_port(f'[::]:{grpc_port}')
    grpc_server.start()
    
    print(f"✅ TCP Viewer gRPC Server started on port {grpc_port}")
    
    # Start HTTP bridge server
    http_server = HTTPServer(('0.0.0.0', http_port), HTTPBridge)
    http_thread = Thread(target=http_server.serve_forever, daemon=True)
    http_thread.start()
    
    print(f"✅ HTTP Bridge started on port {http_port}")
    print(f"   Access: http://localhost:{http_port}/api/traffic")
    print()
    
    # Start background packet capture
    start_packet_capture(interface='lo')
    
    print()
    print("Note: Packet capture requires root/sudo privileges")
    print("Press Ctrl+C to stop")
    print()
    
    try:
        grpc_server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        grpc_server.stop(0)
        http_server.shutdown()


if __name__ == '__main__':
    import sys
    import os
    
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Packet capture may fail.")
        print("Run with: sudo venv/bin/python3 server_with_http.py")
    
    serve()
