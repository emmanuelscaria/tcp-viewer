import React, { useState, useEffect, useRef } from 'react';
import './App.css';

function App() {
  const [connections, setConnections] = useState({});
  const [packets, setPackets] = useState([]);
  const [selectedConnection, setSelectedConnection] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [interface_, setInterface] = useState('eth0');
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
    
    // Connect to HTTP bridge endpoint
    console.log(`Starting monitoring on interface: ${interface_}`);
    
    // Poll the backend HTTP endpoint
    const pollInterval = setInterval(() => {
      fetch('http://localhost:50052/api/traffic')
        .then(res => res.json())
        .then(data => {
          console.log('Received data:', data); // Debug log
          setIsConnected(true);
          
          // Update packets
          if (data.packets && data.packets.length > 0) {
            setPackets(data.packets);
          }
          
          // Update connections
          if (data.connections && data.connections.length > 0) {
            const connectionsMap = {};
            data.connections.forEach(conn => {
              connectionsMap[conn.connection_id] = conn;
            });
            setConnections(connectionsMap);
          }
        })
        .catch(error => {
          console.error('Backend connection failed:', error);
          setIsConnected(false);
        });
    }, 1000); // Poll every second
    
    wsRef.current = { close: () => clearInterval(pollInterval) };
  };

  const stopMonitoring = () => {
    setIsMonitoring(false);
    setIsConnected(false);
    if (wsRef.current) {
      wsRef.current.close();
    }
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
              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>Endpoints</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Source</div>
                    <div className="detail-value">
                      {connections[selectedConnection].src_ip}:{connections[selectedConnection].src_port}
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Destination</div>
                    <div className="detail-value">
                      {connections[selectedConnection].dst_ip}:{connections[selectedConnection].dst_port}
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>State</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">TCP State</div>
                    <div className="detail-value state-badge">{connections[selectedConnection].state}</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Connection ID</div>
                    <div className="detail-value" style={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>
                      {connections[selectedConnection].connection_id}
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>Traffic Statistics</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Bytes Sent</div>
                    <div className="detail-value">
                      {(connections[selectedConnection].bytes_sent || 0).toLocaleString()} bytes
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Bytes Received</div>
                    <div className="detail-value">
                      {(connections[selectedConnection].bytes_received || 0).toLocaleString()} bytes
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Total Traffic</div>
                    <div className="detail-value">
                      {((connections[selectedConnection].bytes_sent || 0) + 
                        (connections[selectedConnection].bytes_received || 0)).toLocaleString()} bytes
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>TCP Control Block (tcpcb)</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Congestion Window (cwnd)</div>
                    <div className="detail-value">{connections[selectedConnection].snd_cwnd || 'N/A'}</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Slow Start Threshold</div>
                    <div className="detail-value">{connections[selectedConnection].snd_ssthresh || 'N/A'}</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Send Window</div>
                    <div className="detail-value">{connections[selectedConnection].snd_wnd || 'N/A'}</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Receive Window</div>
                    <div className="detail-value">{connections[selectedConnection].rcv_wnd || 'N/A'}</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Smoothed RTT</div>
                    <div className="detail-value">{connections[selectedConnection].srtt || 'N/A'} µs</div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Retransmission Timeout</div>
                    <div className="detail-value">{connections[selectedConnection].rto || 'N/A'} ms</div>
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
