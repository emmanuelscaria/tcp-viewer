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

  const formatBytes = (bytes) => {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatRtt = (microseconds) => {
    if (!microseconds) return 'N/A';
    if (microseconds < 1000) return `${microseconds} µs`;
    if (microseconds < 1000000) return `${(microseconds / 1000).toFixed(2)} ms`;
    return `${(microseconds / 1000000).toFixed(2)} s`;
  };

  const getCongestionState = (conn) => {
    if (!conn.snd_cwnd || !conn.snd_ssthresh) return 'Unknown';
    if (conn.snd_cwnd < conn.snd_ssthresh) return 'Slow Start';
    return 'Congestion Avoidance';
  };

  const getStateColor = (state) => {
    const colors = {
      'ESTABLISHED': '#00aa00',
      'SYN_SENT': '#ffaa00',
      'SYN_RECV': '#ffaa00',
      'FIN_WAIT1': '#ff6600',
      'FIN_WAIT2': '#ff6600',
      'TIME_WAIT': '#888888',
      'CLOSE': '#cc0000',
      'CLOSE_WAIT': '#ff6600',
      'LAST_ACK': '#888888',
      'LISTEN': '#0099ff',
      'CLOSING': '#ff6600'
    };
    return colors[state] || '#888888';
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
                    <span 
                      className="state-badge"
                      style={{ 
                        backgroundColor: getStateColor(conn.state),
                        color: 'white',
                        padding: '0.2rem 0.6rem',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        fontWeight: 'bold'
                      }}
                    >
                      {conn.state}
                    </span>
                  </td>
                  <td>{formatBytes(conn.bytes_sent)}</td>
                  <td>{formatBytes(conn.bytes_received)}</td>
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
                      {formatBytes(connections[selectedConnection].bytes_sent || 0)}
                      <span style={{ fontSize: '0.8rem', color: '#888', marginLeft: '0.5rem' }}>
                        ({(connections[selectedConnection].bytes_sent || 0).toLocaleString()})
                      </span>
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Bytes Received</div>
                    <div className="detail-value">
                      {formatBytes(connections[selectedConnection].bytes_received || 0)}
                      <span style={{ fontSize: '0.8rem', color: '#888', marginLeft: '0.5rem' }}>
                        ({(connections[selectedConnection].bytes_received || 0).toLocaleString()})
                      </span>
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Total Traffic</div>
                    <div className="detail-value">
                      {formatBytes((connections[selectedConnection].bytes_sent || 0) + 
                        (connections[selectedConnection].bytes_received || 0))}
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>
                  Congestion Control 
                  <span style={{ 
                    marginLeft: '1rem', 
                    fontSize: '0.85rem', 
                    color: '#00aa00',
                    fontWeight: 'normal'
                  }}>
                    ({getCongestionState(connections[selectedConnection])})
                  </span>
                </h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Congestion Window (cwnd)</div>
                    <div className="detail-value" style={{ color: '#00aaff', fontWeight: 'bold' }}>
                      {connections[selectedConnection].snd_cwnd || 'N/A'} segments
                    </div>
                    <div className="detail-help">
                      Current number of unacknowledged segments allowed
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Slow Start Threshold (ssthresh)</div>
                    <div className="detail-value" style={{ color: '#ffaa00', fontWeight: 'bold' }}>
                      {connections[selectedConnection].snd_ssthresh || 'N/A'} segments
                    </div>
                    <div className="detail-help">
                      Threshold to switch from slow start to congestion avoidance
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Window Utilization</div>
                    <div className="detail-value">
                      {connections[selectedConnection].snd_cwnd && connections[selectedConnection].snd_ssthresh
                        ? `${((connections[selectedConnection].snd_cwnd / connections[selectedConnection].snd_ssthresh) * 100).toFixed(1)}%`
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      cwnd / ssthresh ratio
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>Flow Control</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Send Window (snd_wnd)</div>
                    <div className="detail-value">
                      {connections[selectedConnection].snd_wnd 
                        ? formatBytes(connections[selectedConnection].snd_wnd)
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      Advertised receiver window size
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Receive Window (rcv_wnd)</div>
                    <div className="detail-value">
                      {connections[selectedConnection].rcv_wnd 
                        ? formatBytes(connections[selectedConnection].rcv_wnd)
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      Local receive buffer space
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Effective Window</div>
                    <div className="detail-value">
                      {connections[selectedConnection].snd_cwnd && connections[selectedConnection].snd_wnd
                        ? formatBytes(Math.min(
                            connections[selectedConnection].snd_cwnd * 1460, // Assume 1460 MSS
                            connections[selectedConnection].snd_wnd
                          ))
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      min(cwnd × MSS, snd_wnd)
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>Round-Trip Time & Retransmission</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Smoothed RTT (srtt)</div>
                    <div className="detail-value" style={{ 
                      color: connections[selectedConnection].srtt > 100000 ? '#ff6600' : '#00aa00',
                      fontWeight: 'bold'
                    }}>
                      {formatRtt(connections[selectedConnection].srtt)}
                    </div>
                    <div className="detail-help">
                      Exponentially weighted moving average of RTT
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">RTT (Milliseconds)</div>
                    <div className="detail-value">
                      {connections[selectedConnection].srtt 
                        ? `${(connections[selectedConnection].srtt / 1000).toFixed(3)} ms`
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      RTT in milliseconds for easier reading
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Retransmission Timeout (RTO)</div>
                    <div className="detail-value" style={{ color: '#ffaa00' }}>
                      {connections[selectedConnection].rto || 'N/A'} ms
                    </div>
                    <div className="detail-help">
                      Time before retransmitting unacked data
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Latency Category</div>
                    <div className="detail-value">
                      {!connections[selectedConnection].srtt ? 'Unknown' :
                       connections[selectedConnection].srtt < 1000 ? '🟢 Excellent (<1ms)' :
                       connections[selectedConnection].srtt < 50000 ? '🟢 Good (<50ms)' :
                       connections[selectedConnection].srtt < 150000 ? '🟡 Fair (<150ms)' :
                       '🔴 High (>150ms)'}
                    </div>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3 style={{ marginBottom: '1rem', fontSize: '1rem', color: '#888' }}>Performance Insights</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <div className="detail-label">Bandwidth-Delay Product</div>
                    <div className="detail-value">
                      {connections[selectedConnection].snd_cwnd && connections[selectedConnection].srtt
                        ? formatBytes((connections[selectedConnection].snd_cwnd * 1460))
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      cwnd × MSS (optimal buffer size)
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Theoretical Max Throughput</div>
                    <div className="detail-value">
                      {connections[selectedConnection].snd_cwnd && connections[selectedConnection].srtt
                        ? `${((connections[selectedConnection].snd_cwnd * 1460 * 8) / (connections[selectedConnection].srtt / 1000000) / 1000000).toFixed(2)} Mbps`
                        : 'N/A'}
                    </div>
                    <div className="detail-help">
                      (cwnd × MSS × 8) / RTT
                    </div>
                  </div>
                  <div className="detail-item">
                    <div className="detail-label">Connection Age</div>
                    <div className="detail-value">
                      {connections[selectedConnection].timestamp 
                        ? `${Math.floor((Date.now() - new Date(connections[selectedConnection].timestamp)) / 1000)}s ago`
                        : 'N/A'}
                    </div>
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
