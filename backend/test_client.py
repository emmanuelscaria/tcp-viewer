#!/usr/bin/env python3
"""Quick test to verify backend is working"""
import grpc
import tcp_monitor_pb2
import tcp_monitor_pb2_grpc

def test_connection():
    channel = grpc.insecure_channel('localhost:50051')
    stub = tcp_monitor_pb2_grpc.TcpMonitorStub(channel)
    
    request = tcp_monitor_pb2.MonitorRequest(interface_name='lo')
    
    print("Connecting to backend gRPC server...")
    try:
        count = 0
        for event in stub.StreamTraffic(request):
            if event.HasField('packet'):
                pkt = event.packet
                print(f"[PACKET] {pkt.src_ip}:{pkt.src_port} → {pkt.dst_ip}:{pkt.dst_port}")
            elif event.HasField('stats'):
                stats = event.stats
                print(f"[STATS] {stats.connection_id} state={stats.state}")
            
            count += 1
            if count >= 10:  # Show first 10 events
                print(f"\n✅ Backend is working! Received {count} events.")
                break
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    test_connection()
