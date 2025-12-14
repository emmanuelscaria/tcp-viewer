#!/usr/bin/env python3
"""
Example: Different ways to identify TCP connections
"""

import hashlib

def connection_id_unidirectional(src_ip, src_port, dst_ip, dst_port):
    """
    Current implementation: Each direction is a separate connection
    A->B and B->A are different connections
    """
    conn_str = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
    return hashlib.md5(conn_str.encode()).hexdigest()[:16]


def connection_id_bidirectional(src_ip, src_port, dst_ip, dst_port):
    """
    Alternative: Treat both directions as same connection
    A->B and B->A get the same connection ID
    """
    # Sort the endpoints to create consistent ID regardless of direction
    endpoints = sorted([
        (src_ip, src_port),
        (dst_ip, dst_port)
    ])
    conn_str = f"{endpoints[0][0]}:{endpoints[0][1]}-{endpoints[1][0]}:{endpoints[1][1]}"
    return hashlib.md5(conn_str.encode()).hexdigest()[:16]


# Example usage
if __name__ == '__main__':
    # Packet 1: Client -> Server
    pkt1_src_ip = "192.168.1.100"
    pkt1_src_port = 54321
    pkt1_dst_ip = "93.184.216.34"  # example.com
    pkt1_dst_port = 443
    
    # Packet 2: Server -> Client (response)
    pkt2_src_ip = "93.184.216.34"
    pkt2_src_port = 443
    pkt2_dst_ip = "192.168.1.100"
    pkt2_dst_port = 54321
    
    print("=== Unidirectional (Current Implementation) ===")
    id1_uni = connection_id_unidirectional(pkt1_src_ip, pkt1_src_port, pkt1_dst_ip, pkt1_dst_port)
    id2_uni = connection_id_unidirectional(pkt2_src_ip, pkt2_src_port, pkt2_dst_ip, pkt2_dst_port)
    print(f"Client->Server: {id1_uni}")
    print(f"Server->Client: {id2_uni}")
    print(f"Same connection? {id1_uni == id2_uni}")
    
    print("\n=== Bidirectional (Alternative) ===")
    id1_bi = connection_id_bidirectional(pkt1_src_ip, pkt1_src_port, pkt1_dst_ip, pkt1_dst_port)
    id2_bi = connection_id_bidirectional(pkt2_src_ip, pkt2_src_port, pkt2_dst_ip, pkt2_dst_port)
    print(f"Client->Server: {id1_bi}")
    print(f"Server->Client: {id2_bi}")
    print(f"Same connection? {id1_bi == id2_bi}")
    
    print("\n=== TCP 4-Tuple Identification ===")
    print("Source IP:        " + pkt1_src_ip + " (from IP header)")
    print("Source Port:      " + str(pkt1_src_port) + " (from TCP header)")
    print("Destination IP:   " + pkt1_dst_ip + " (from IP header)")
    print("Destination Port: " + str(pkt1_dst_port) + " (from TCP header)")
    print("\nThis uniquely identifies a TCP connection!")
