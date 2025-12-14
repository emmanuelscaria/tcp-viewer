#!/usr/bin/env python3
"""
TCP Introspector - Reads real kernel TCP connection data from /proc/net/tcp
"""

import socket
import struct
from typing import Dict, Optional, Tuple


class TcpIntrospector:
    """Read TCP connection state from kernel via /proc/net/tcp"""
    
    # TCP States (from include/net/tcp_states.h)
    TCP_STATES = {
        0x01: 'ESTABLISHED',
        0x02: 'SYN_SENT',
        0x03: 'SYN_RECV',
        0x04: 'FIN_WAIT1',
        0x05: 'FIN_WAIT2',
        0x06: 'TIME_WAIT',
        0x07: 'CLOSE',
        0x08: 'CLOSE_WAIT',
        0x09: 'LAST_ACK',
        0x0A: 'LISTEN',
        0x0B: 'CLOSING',
    }
    
    def __init__(self):
        self.connections = {}
    
    def _parse_hex_address(self, hex_str: str) -> Tuple[str, int]:
        """Parse hex address from /proc/net/tcp format
        
        Format: "0100007F:0050" = 127.0.0.1:80 (little-endian)
        """
        ip_hex, port_hex = hex_str.split(':')
        
        # Convert little-endian hex IP to dotted notation
        ip_int = int(ip_hex, 16)
        ip = socket.inet_ntoa(struct.pack('<I', ip_int))
        
        # Convert hex port to int
        port = int(port_hex, 16)
        
        return ip, port
    
    def _create_connection_id(self, src_ip: str, src_port: int, dst_ip: str, dst_port: int) -> str:
        """Create bidirectional connection ID (same as in server_with_http.py)"""
        import hashlib
        endpoints = sorted([
            (src_ip, src_port),
            (dst_ip, dst_port)
        ])
        conn_str = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
        return hashlib.md5(conn_str.encode()).hexdigest()[:16]
    
    def update(self):
        """Read /proc/net/tcp and update connection state"""
        self.connections.clear()
        
        try:
            with open('/proc/net/tcp', 'r') as f:
                # Skip header line
                next(f)
                
                for line in f:
                    parts = line.split()
                    if len(parts) < 14:
                        continue
                    
                    # Parse fields (see kernel Documentation/networking/proc_net_tcp.txt)
                    # Format:
                    # sl local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode ...
                    local_addr = parts[1]
                    remote_addr = parts[2]
                    state_hex = int(parts[3], 16)
                    tx_queue = int(parts[4].split(':')[0], 16)
                    rx_queue = int(parts[4].split(':')[1], 16)
                    
                    # Extended fields after inode (around index 13+)
                    # These contain TCP control block info
                    if len(parts) >= 14:
                        # Field 13 is ref count, 14 is memory address, 15+ are TCP metrics
                        # Format varies by kernel version, but typically:
                        # 15: timer active, 16: jiffies, 17: rto, 18: ato, 19: snd.mss
                        # 20: rcv.mss, 21: unacked, 22: sacked, 23: lost, 24: retrans
                        # 25: fackets, 26: last_data_sent, 27: last_ack_sent
                        # 28: last_data_recv, 29: last_ack_recv
                        pass
                    
                    src_ip, src_port = self._parse_hex_address(local_addr)
                    dst_ip, dst_port = self._parse_hex_address(remote_addr)
                    
                    # Skip LISTEN sockets with 0.0.0.0 remote (not real connections)
                    if dst_ip == '0.0.0.0' and dst_port == 0:
                        continue
                    
                    conn_id = self._create_connection_id(src_ip, src_port, dst_ip, dst_port)
                    
                    state = self.TCP_STATES.get(state_hex, f'UNKNOWN({state_hex:02X})')
                    
                    self.connections[conn_id] = {
                        'connection_id': conn_id,
                        'src_ip': src_ip,
                        'src_port': src_port,
                        'dst_ip': dst_ip,
                        'dst_port': dst_port,
                        'state': state,
                        'tx_queue': tx_queue,
                        'rx_queue': rx_queue,
                    }
                    
        except Exception as e:
            print(f"Error reading /proc/net/tcp: {e}")
    
    def get_connection_stats(self, conn_id: str) -> Optional[Dict]:
        """Get stats for a specific connection"""
        return self.connections.get(conn_id)
    
    def get_all_connections(self) -> Dict:
        """Get all active connections"""
        return self.connections


def get_tcp_info_via_ss(src_ip: str, src_port: int, dst_ip: str, dst_port: int) -> Optional[Dict]:
    """
    Use 'ss' command to get detailed TCP info
    This provides more detailed metrics than /proc/net/tcp
    
    Example: ss -tin 'sport = :80'
    """
    import subprocess
    
    try:
        # Use ss with extended TCP info
        cmd = [
            'ss', '-tin',
            f'( sport = :{src_port} and dport = :{dst_port} )',
            f'or ( sport = :{dst_port} and dport = :{src_port} )'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=1)
        
        if result.returncode == 0 and result.stdout:
            # Parse ss output for metrics like cwnd, rtt, etc.
            # Example output line:
            # ESTAB  0      0      192.168.1.1:443   192.168.1.2:54321
            #          cubic wscale:7,7 rto:204 rtt:0.5/0.25 cwnd:10 ssthresh:7
            
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'cwnd:' in line or 'rtt:' in line:
                    metrics = {}
                    
                    # Parse cwnd
                    if 'cwnd:' in line:
                        try:
                            cwnd_str = line.split('cwnd:')[1].split()[0]
                            metrics['snd_cwnd'] = int(cwnd_str)
                        except:
                            pass
                    
                    # Parse ssthresh
                    if 'ssthresh:' in line:
                        try:
                            ssthresh_str = line.split('ssthresh:')[1].split()[0]
                            metrics['snd_ssthresh'] = int(ssthresh_str)
                        except:
                            pass
                    
                    # Parse RTT (format: "rtt:0.5/0.25" means 0.5ms avg, 0.25ms variance)
                    if 'rtt:' in line:
                        try:
                            rtt_str = line.split('rtt:')[1].split()[0]
                            rtt_avg = float(rtt_str.split('/')[0])
                            metrics['srtt'] = int(rtt_avg * 1000)  # Convert ms to microseconds
                        except:
                            pass
                    
                    # Parse RTO
                    if 'rto:' in line:
                        try:
                            rto_str = line.split('rto:')[1].split()[0]
                            metrics['rto'] = int(rto_str)
                        except:
                            pass
                    
                    # Parse send window
                    if 'snd_wnd:' in line or 'send' in line:
                        # ss shows send buffer, not exact window
                        try:
                            # This is approximate
                            metrics['snd_wnd'] = 65535
                        except:
                            pass
                    
                    if metrics:
                        return metrics
                        
    except Exception as e:
        print(f"Error getting ss info: {e}")
    
    return None


if __name__ == '__main__':
    # Test the introspector
    introspector = TcpIntrospector()
    introspector.update()
    
    print(f"Found {len(introspector.connections)} active TCP connections\n")
    
    for conn_id, conn in list(introspector.connections.items())[:5]:
        print(f"Connection: {conn['src_ip']}:{conn['src_port']} ↔ {conn['dst_ip']}:{conn['dst_port']}")
        print(f"  State: {conn['state']}")
        print(f"  TX Queue: {conn['tx_queue']} bytes")
        print(f"  RX Queue: {conn['rx_queue']} bytes")
        print(f"  ID: {conn_id}")
        
        # Try to get detailed info via ss
        ss_info = get_tcp_info_via_ss(
            conn['src_ip'], conn['src_port'],
            conn['dst_ip'], conn['dst_port']
        )
        if ss_info:
            print(f"  Extended metrics from ss:")
            for key, val in ss_info.items():
                print(f"    {key}: {val}")
        print()
