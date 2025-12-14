import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [connections, setConnections] = useState({});
  const [packets, setPackets] = useState([]);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [interface_, setInterface] = useState('lo');
  const [isMonitoring, setIsMonitoring] = useState(false);
  
  const maxPackets = 100; // Keep last 100 packets for display
  const wsRef = useRef(null);

  useEffect(() => {
    // Cleanup on unmount
    return () => {
      // eslint-disable-next-line react-hooks/exhaustive-deps
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const startMonitoring = () => {
    if (isMonitoring) return;
    
    setIsMonitoring(true);
    setIsConnected(false);
    
    // Note: This is a placeholder for gRPC-Web connection
    // In production, you would use generated gRPC-Web client
    // For now, we'll simulate with WebSocket as a demonstration
    
    try {
      // Simulated connection - replace with actual gRPC-Web client
      console.log(`Starting monitoring on interface: ${interface_}`);
      setIsConnected(true);
      
      // TODO: Initialize gRPC-Web client here
      // const client = new TcpMonitorClient('http://localhost:8080');
      // const stream = client.streamTraffic({ interface_name: interface_ });
      // stream.on('data', handleTcpEvent);
      
      // Simulated data for demonstration
      simulateData();
      
    } catch (error) {
      console.error('Connection failed:', error);
      setIsConnected(false);
      setIsMonitoring(false);
    }
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    setIsConnected(false);
    if (wsRef.current) {
      wsRef.current.close();
    }
  };

  // Simulated data generator (replace with real gRPC data)
  const simulateData = () => {
    let counter = 0;
    const interval = setInterval(() => {
      if (!isMonitoring) {
        clearInterval(interval);
        return;
      }
      
      // Simulate packet
      const packet = {
        timestamp: new Date().toISOString(),
        src_ip: '127.0.0.1',
        src_port: 8000 + Math.floor(Math.random() * 100),
        dst_ip: '127.0.0.1',
        dst_port: 50051,
        flag_syn: counter % 10 === 0,
        flag_ack: true,
        flag_fin: counter % 15 === 0,
        flag_rst: false,
        flag_psh: counter % 3 === 0,
        flag_urg: false,
        payload_length: Math.floor(Math.random() * 1500),
        seq_number: 1000 + counter,
        ack_number: 2000 + counter,
      };
      
      handlePacket(packet);
      
      // Simulate connection stats every second
      if (counter % 10 === 0) {
        const connId = `conn_${Math.floor(counter / 10) % 3}`;
        const stats = {
          connection_id: connId,
          src_ip: '127.0.0.1',
          src_port: 8000,
          dst_ip: '127.0.0.1',
          dst_port: 50051,
          state: ['ESTABLISHED', 'SYN_SENT', 'FIN_WAIT'][Math.floor(Math.random() * 3)],
          snd_cwnd: Math.floor(Math.random() * 100),
          snd_ssthresh: 64,
          snd_wnd: 65535,
          rcv_wnd: 65535,
          srtt: Math.floor(Math.random() * 5000),
          rto: 200,
          bytes_sent: counter * 100,
          bytes_received: counter * 80,
          timestamp: new Date().toISOString(),
        };
        handleConnectionStats(stats);
      }
      
      counter++;
    }, 100);
  };

  const handlePacket = (packet) => {
    setPackets(prev => {
      const newPackets = [packet, ...prev];
      return newPackets.slice(0, maxPackets);
    });
  };

  const handleConnectionStats = (stats) => {
    setConnections(prev => ({
      ...prev,
      [stats.connection_id]: stats
    }));
  };

  const formatFlags = (packet) => {
    const flags = [];
    if (packet.flag_syn) flags.push('SYN');
    if (packet.flag_ack) flags.push('ACK');
    if (packet.flag_fin) flags.push('FIN');
    if (packet.flag_rst) flags.push('RST');
    if (packet.flag_psh) flags.push('PSH');
    if (packet.flag_urg) flags.push('URG');
    return flags.join(',');
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString() + '.' + date.getMilliseconds();
  };

  return (
    <div className="App">
      <header className="header">
        <h1>TCP Viewer</h1>
        <div className="status">
          <div className={`status-indicator ${isConnected ? 'connected' : ''}`}></div>
          <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </header>
      
      <div className="controls">
        <label>
          Interface:
          <input 
            type="text" 
            value={interface_} 
            onChange={(e) => setInterface(e.target.value)}
            disabled={isMonitoring}
          />
        </label>
        <button 
          onClick={isMonitoring ? stopMonitoring : startMonitoring}
          style={{ backgroundColor: isMonitoring ? '#cc0000' : '#00aa00' }}
        >
          {isMonitoring ? 'Stop Monitoring' : 'Start Monitoring'}
        </button>
      </div>
      
      <div className="main-content">
        <div className="panel left-panel">
          <h2 className="section-title">Active Connections ({Object.keys(connections).length})</h2>
          <table className="connections-table">
            <thead>
              <tr>
                <th>Source</th>
                <th>Destination</th>
                <th>State</th>
                <th>Bytes Sent</th>
                <th>Bytes Recv</th>
              </tr>
            </thead>
            <tbody>
              {Object.values(connections).map(conn => (
                <tr 
                  key={conn.connection_id}
                  className={selectedConnection === conn.connection_id ? 'selected' : ''}
                  onClick={() => setSelectedConnection(conn.connection_id)}
                >
                  <td>{conn.src_ip}:{conn.src_port}</td>
                  <td>{conn.dst_ip}:{conn.dst_port}</td>
                  <td>
                    <span className={`state-badge state-${conn.state}`}>
                      {conn.state}
                    </span>
                  </td>
                  <td>{conn.bytes_sent.toLocaleString()}</td>
                  <td>{conn.bytes_received.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          <h2 className="section-title" style={{ marginTop: '2rem' }}>Packet Stream</h2>
          <div className="packet-stream">
            {packets.map((pkt, idx) => (
              <div key={idx} className="packet-entry">
                <span className="packet-time">{formatTime(pkt.timestamp)}</span>
                <span className="packet-info">
                  {pkt.src_ip}:{pkt.src_port} → {pkt.dst_ip}:{pkt.dst_port}
                </span>
                <span className="packet-flags">[{formatFlags(pkt)}]</span>
                <span>{pkt.payload_length}B</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="panel right-panel">
          <h2 className="section-title">Connection Details</h2>
          {selectedConnection && connections[selectedConnection] ? (
            <div>
              <div className="detail-grid">
                <div className="detail-item">
                  <div className="detail-label">State</div>
                  <div className="detail-value">{connections[selectedConnection].state}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Congestion Window (cwnd)</div>
                  <div className="detail-value">{connections[selectedConnection].snd_cwnd}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Slow Start Threshold</div>
                  <div className="detail-value">{connections[selectedConnection].snd_ssthresh}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Send Window</div>
                  <div className="detail-value">{connections[selectedConnection].snd_wnd}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Receive Window</div>
                  <div className="detail-value">{connections[selectedConnection].rcv_wnd}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Smoothed RTT (µs)</div>
                  <div className="detail-value">{connections[selectedConnection].srtt}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">RTO (ms)</div>
                  <div className="detail-value">{connections[selectedConnection].rto}</div>
                </div>
                <div className="detail-item">
                  <div className="detail-label">Connection ID</div>
                  <div className="detail-value" style={{ fontSize: '0.9rem' }}>
                    {connections[selectedConnection].connection_id}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="no-selection">
              Select a connection from the left panel to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
