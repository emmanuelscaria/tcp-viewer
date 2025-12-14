#!/usr/bin/env python3
"""
TCP Packet Analyzer - Derives TCP metrics from packet data
This module calculates RTT, congestion window estimates, and other metrics
by analyzing packet sequences and timestamps instead of reading kernel state.
"""

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Tuple


@dataclass
class PacketRecord:
    """Records a single TCP packet for analysis"""
    timestamp: float
    seq: int
    ack: int
    flags: str
    payload_len: int
    window: int
    is_outgoing: bool  # True if packet is from connection initiator


@dataclass
class ConnectionMetrics:
    """Calculated TCP metrics for a connection"""
    # RTT Estimation (using timestamp-based sampling)
    rtt_samples: deque = field(default_factory=lambda: deque(maxlen=10))
    srtt: float = 0.0  # Smoothed RTT in milliseconds
    rtt_var: float = 0.0  # RTT variation
    rto: float = 1000.0  # Retransmission timeout in milliseconds
    
    # Congestion Window Estimation
    cwnd_estimate: int = 10  # Estimated congestion window (in segments)
    ssthresh: int = 64  # Slow start threshold
    
    # Window Tracking
    advertised_window: int = 65535  # Last advertised receive window
    remote_window: int = 65535  # Remote peer's advertised window
    
    # Sequence tracking
    last_seq: int = 0
    last_ack: int = 0
    next_expected_seq: int = 0
    
    # Performance metrics
    bytes_sent: int = 0
    bytes_received: int = 0
    segments_sent: int = 0
    segments_received: int = 0
    retransmissions: int = 0
    
    # Timing
    last_packet_time: float = 0.0
    connection_start: float = 0.0
    
    # Inflight tracking for cwnd estimation
    unacked_packets: Dict[int, float] = field(default_factory=dict)  # seq -> timestamp
    max_inflight: int = 0


class TcpPacketAnalyzer:
    """Analyzes TCP packets to derive connection metrics"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionMetrics] = defaultdict(ConnectionMetrics)
        
    def process_packet(self, conn_id: str, pkt_data: dict, is_outgoing: bool) -> ConnectionMetrics:
        """
        Process a packet and update connection metrics
        
        Args:
            conn_id: Unique connection identifier
            pkt_data: Dictionary with packet fields (seq, ack, flags, payload_len, window, timestamp)
            is_outgoing: True if packet is from initiator to responder
            
        Returns:
            Updated ConnectionMetrics for this connection
        """
        metrics = self.connections[conn_id]
        
        if metrics.connection_start == 0.0:
            metrics.connection_start = pkt_data['timestamp']
        
        # Extract packet fields
        seq = pkt_data.get('seq', 0)
        ack = pkt_data.get('ack', 0)
        flags = pkt_data.get('flags', '')
        payload_len = pkt_data.get('payload_len', 0)
        window = pkt_data.get('window', 65535)
        timestamp = pkt_data['timestamp']
        
        # Update window sizes
        if is_outgoing:
            metrics.advertised_window = window
            metrics.bytes_sent += payload_len
            metrics.segments_sent += 1
            
            # Track unacknowledged data for RTT calculation
            if payload_len > 0 or 'S' in flags or 'F' in flags:
                metrics.unacked_packets[seq] = timestamp
                metrics.last_seq = seq
                
        else:
            metrics.remote_window = window
            metrics.bytes_received += payload_len
            metrics.segments_received += 1
            
            # Process ACKs for RTT calculation
            if 'A' in flags and ack > 0:
                self._process_ack(metrics, ack, timestamp)
                metrics.last_ack = ack
        
        # Detect retransmissions (simplified)
        if is_outgoing and payload_len > 0:
            if seq < metrics.last_seq:
                metrics.retransmissions += 1
                # Retransmission indicates congestion - reduce cwnd estimate
                metrics.ssthresh = max(metrics.cwnd_estimate // 2, 2)
                metrics.cwnd_estimate = metrics.ssthresh
        
        # Estimate congestion window based on inflight data
        self._update_cwnd_estimate(metrics)
        
        metrics.last_packet_time = timestamp
        
        return metrics
    
    def _process_ack(self, metrics: ConnectionMetrics, ack: int, timestamp: float):
        """Process an ACK packet to calculate RTT"""
        # Find matching sent packet
        acked_packets = []
        for seq, sent_time in metrics.unacked_packets.items():
            if seq < ack:  # This packet has been acknowledged
                acked_packets.append((seq, sent_time))
        
        # Calculate RTT for the most recent acked packet
        if acked_packets:
            # Take the latest sent packet that was acked
            acked_packets.sort(key=lambda x: x[1], reverse=True)
            latest_seq, sent_time = acked_packets[0]
            
            rtt_sample = (timestamp - sent_time) * 1000  # Convert to milliseconds
            
            # Only consider reasonable RTT values (0.1ms to 10s)
            if 0.1 <= rtt_sample <= 10000:
                metrics.rtt_samples.append(rtt_sample)
                
                # Update SRTT using exponential weighted moving average
                # SRTT = (1 - alpha) * SRTT + alpha * RTT_sample, where alpha = 0.125
                if metrics.srtt == 0:
                    metrics.srtt = rtt_sample
                    metrics.rtt_var = rtt_sample / 2
                else:
                    alpha = 0.125
                    beta = 0.25
                    metrics.rtt_var = (1 - beta) * metrics.rtt_var + beta * abs(metrics.srtt - rtt_sample)
                    metrics.srtt = (1 - alpha) * metrics.srtt + alpha * rtt_sample
                
                # Calculate RTO (Retransmission Timeout)
                # RTO = SRTT + 4 * RTT_VAR, with bounds [200ms, 60s]
                metrics.rto = max(200, min(60000, metrics.srtt + 4 * metrics.rtt_var))
            
            # Remove acked packets
            for seq, _ in acked_packets:
                metrics.unacked_packets.pop(seq, None)
    
    def _update_cwnd_estimate(self, metrics: ConnectionMetrics):
        """
        Estimate congestion window based on inflight data
        This is an approximation since we can't directly read kernel's cwnd
        """
        inflight = len(metrics.unacked_packets)
        
        # Track maximum inflight packets
        if inflight > metrics.max_inflight:
            metrics.max_inflight = inflight
        
        # Simple cwnd estimation:
        # During slow start, cwnd grows exponentially
        # During congestion avoidance, cwnd grows linearly
        
        # If we're successfully sending more data, increase estimate
        if inflight >= metrics.cwnd_estimate and metrics.retransmissions == 0:
            if metrics.cwnd_estimate < metrics.ssthresh:
                # Slow start: exponential growth
                metrics.cwnd_estimate = min(metrics.cwnd_estimate * 2, metrics.ssthresh)
            else:
                # Congestion avoidance: linear growth
                metrics.cwnd_estimate += 1
        
        # Cap cwnd estimate by receiver window
        metrics.cwnd_estimate = min(metrics.cwnd_estimate, metrics.remote_window // 1460)
        
        # Ensure minimum cwnd
        metrics.cwnd_estimate = max(2, metrics.cwnd_estimate)
    
    def get_metrics(self, conn_id: str) -> Optional[Dict]:
        """Get current metrics for a connection"""
        if conn_id not in self.connections:
            return None
        
        metrics = self.connections[conn_id]
        
        return {
            'srtt': int(metrics.srtt),
            'rto': int(metrics.rto),
            'snd_cwnd': metrics.cwnd_estimate,
            'snd_ssthresh': metrics.ssthresh,
            'snd_wnd': metrics.remote_window,
            'rcv_wnd': metrics.advertised_window,
            'bytes_sent': metrics.bytes_sent,
            'bytes_received': metrics.bytes_received,
            'segments_sent': metrics.segments_sent,
            'segments_received': metrics.segments_received,
            'retransmissions': metrics.retransmissions,
            'rtt_samples': list(metrics.rtt_samples),
            'inflight': len(metrics.unacked_packets),
            'max_inflight': metrics.max_inflight,
        }
    
    def cleanup_old_connections(self, timeout: float = 300.0):
        """Remove connections that haven't seen packets in timeout seconds"""
        current_time = time.time()
        to_remove = []
        
        for conn_id, metrics in self.connections.items():
            if current_time - metrics.last_packet_time > timeout:
                to_remove.append(conn_id)
        
        for conn_id in to_remove:
            del self.connections[conn_id]
