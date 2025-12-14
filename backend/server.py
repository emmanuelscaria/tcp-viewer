#!/usr/bin/env python3
"""
TCP Viewer - Backend gRPC Server
Captures TCP packets and streams them to the frontend
Requires root privileges for raw socket access
"""

import socket
import struct
import time
import hashlib
from concurrent import futures
from datetime import datetime
import grpc

# Import generated gRPC stubs (will be generated via generate_grpc.sh)
import tcp_monitor_pb2
import tcp_monitor_pb2_grpc

try:
    from scapy.all import sniff, TCP, IP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    print("Warning: Scapy not available. Install with: pip install scapy")


class TcpMonitorService(tcp_monitor_pb2_grpc.TcpMonitorServicer):
    """gRPC service implementation for TCP monitoring"""
    
    def __init__(self):
        self.active_connections = {}
        self.packet_buffer = []
        
    def StreamTraffic(self, request, context):
        """
        Server-side streaming RPC that captures and streams TCP traffic
        
        Args:
            request: MonitorRequest containing interface_name
            context: gRPC context
            
        Yields:
            TcpEvent messages containing packet info or connection stats
        """
        interface = request.interface_name or None
        print(f"Starting packet capture on interface: {interface or 'all'}")
        
        if not SCAPY_AVAILABLE:
            # Send error event
            yield tcp_monitor_pb2.TcpEvent(
                packet=tcp_monitor_pb2.PacketInfo(
                    timestamp=datetime.now().isoformat(),
                    src_ip="ERROR",
                    dst_ip="Scapy not installed",
                )
            )
            return
            
        # Packet callback function
        def packet_handler(pkt):
            if pkt.haslayer(TCP) and pkt.haslayer(IP):
                try:
                    ip_layer = pkt[IP]
                    tcp_layer = pkt[TCP]
                    
                    # Create PacketInfo message
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
                    
                    # Update connection tracking
                    conn_id = self._get_connection_id(
                        ip_layer.src, tcp_layer.sport,
                        ip_layer.dst, tcp_layer.dport
                    )
                    
                    self._update_connection(conn_id, ip_layer, tcp_layer)
                    
                    # Add to buffer
                    self.packet_buffer.append(packet_info)
                    
                except Exception as e:
                    print(f"Error processing packet: {e}")
        
        # Start background sniffing in a separate thread
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
        
        # Stream buffered packets and connection stats
        last_stats_time = time.time()
        
        while context.is_active():
            try:
                # Send buffered packets
                while self.packet_buffer:
                    packet = self.packet_buffer.pop(0)
                    yield tcp_monitor_pb2.TcpEvent(packet=packet)
                
                # Periodically send connection statistics (every 1 second)
                current_time = time.time()
                if current_time - last_stats_time >= 1.0:
                    for conn_id, conn_data in list(self.active_connections.items()):
                        stats = self._get_connection_stats(conn_id, conn_data)
                        yield tcp_monitor_pb2.TcpEvent(stats=stats)
                    last_stats_time = current_time
                
                # Throttle to ~30-60fps as per NFR-09
                time.sleep(0.033)  # ~30fps
                
            except Exception as e:
                print(f"Streaming error: {e}")
                break
    
    def _get_connection_id(self, src_ip, src_port, dst_ip, dst_port):
        """Generate unique connection ID from 4-tuple"""
        conn_str = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
        return hashlib.md5(conn_str.encode()).hexdigest()[:16]
    
    def _update_connection(self, conn_id, ip_layer, tcp_layer):
        """Update connection tracking information"""
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
        
        # Simple state tracking based on flags
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
        
        # Update byte counters
        conn['bytes_sent'] += len(tcp_layer.payload)
        conn['last_seen'] = time.time()
    
    def _get_connection_stats(self, conn_id, conn_data):
        """Create ConnectionStats message from tracked connection"""
        # Note: Real tcpcb values would come from kernel via ss/netlink/eBPF
        # This is a placeholder that returns mock values
        return tcp_monitor_pb2.ConnectionStats(
            connection_id=conn_id,
            src_ip=conn_data['src_ip'],
            src_port=conn_data['src_port'],
            dst_ip=conn_data['dst_ip'],
            dst_port=conn_data['dst_port'],
            state=conn_data['state'],
            snd_cwnd=10,  # Mock value - would read from kernel
            snd_ssthresh=64,  # Mock value
            snd_wnd=65535,  # Mock value
            rcv_wnd=65535,  # Mock value
            srtt=1000,  # Mock value (1ms in microseconds)
            rto=200,  # Mock value (200ms)
            bytes_sent=conn_data['bytes_sent'],
            bytes_received=conn_data['bytes_received'],
            timestamp=datetime.now().isoformat(),
        )


def serve(port=50051):
    """Start the gRPC server"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tcp_monitor_pb2_grpc.add_TcpMonitorServicer_to_server(
        TcpMonitorService(), server
    )
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    
    print(f"TCP Viewer gRPC Server started on port {port}")
    print("Note: Packet capture requires root/sudo privileges")
    print("Press Ctrl+C to stop")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.stop(0)


if __name__ == '__main__':
    import sys
    
    # Check for root privileges
    import os
    if os.geteuid() != 0:
        print("WARNING: Not running as root. Packet capture may fail.")
        print("Run with: sudo python3 server.py")
    
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 50051
    serve(port)
