# TCP Viewer - Changelog

All notable changes to this project are documented in this file.

---

## [1.0.0] - 2025-12-14

### ✨ Major Release - Complete Working Implementation

This release marks the first fully functional version of TCP Viewer with comprehensive documentation.

### 🎉 New Features

#### Core Functionality
- ✅ **Real-time TCP packet capture** using Scapy on Linux
- ✅ **Bidirectional connection tracking** - merges both flow directions
- ✅ **HTTP REST API** on port 50052 (`/api/traffic` endpoint)
- ✅ **React-based web dashboard** with auto-refresh
- ✅ **Round-Trip Time (RTT) estimation** from packet timing
- ✅ **Retransmission detection** via sequence number tracking
- ✅ **TCP state monitoring** from `/proc/net/tcp` + packet flags
- ✅ **Recent packet history** - last 5 packets per connection

#### User Interface
- ✅ **Packet Stream Panel** - live scrolling packet log
- ✅ **Active Connections Table** - clickable rows
- ✅ **Connection Details Panel** - expanded metrics view
- ✅ **Traffic Statistics** - bytes/packets sent & received
- ✅ **Performance Insights** - RTT, throughput, window sizes

#### Developer Experience
- ✅ **Simple HTTP/JSON** - no gRPC complexity
- ✅ **Thread-safe backend** - concurrent packet capture + API
- ✅ **Bounded memory** - max 1000 packets stored
- ✅ **CORS enabled** - easy browser integration

### 📚 Documentation

#### New Documentation Files
- **README.md** - Complete project overview (500+ lines)
- **ARCHITECTURE.md** - System design documentation (400+ lines)
- **API.md** - REST API reference (400+ lines)
- **QUICKSTART.md** - Enhanced step-by-step guide (300+ lines)
- **DOCUMENTATION_INDEX.md** - Documentation navigation guide
- **CHANGELOG.md** - This file

#### Updated Documentation
- Removed all gRPC/protobuf references (simplified to HTTP)
- Added real-world examples and code snippets
- Included troubleshooting guides
- Added performance tuning tips

### 🔧 Technical Changes

#### Backend
- **Server Architecture**: HTTP server + background packet sniffer
- **Packet Processing**: `tcp_packet_analyzer.py` with RTT calculation
- **State Introspection**: `tcp_introspector.py` reads `/proc/net/tcp`
- **Data Storage**: In-memory with thread locks
- **Interface**: Default `eth0` (configurable)

#### Frontend
- **Framework**: React 18 with hooks
- **Polling**: 1-second refresh interval
- **State Management**: React useState for packets/connections
- **Styling**: Custom CSS with modern UI design

### 🐛 Bug Fixes

#### Backend Fixes
- ✅ Fixed connection tracking to merge bidirectional flows
- ✅ Resolved thread safety issues with locks
- ✅ Fixed RTT calculation from packet timestamps
- ✅ Corrected sequence number tracking for retransmissions
- ✅ Fixed connection state inference from packet flags

#### Frontend Fixes
- ✅ Fixed empty connection table rendering
- ✅ Corrected CSS syntax errors (removed duplicate braces)
- ✅ Fixed recent packets display formatting
- ✅ Resolved fetch errors with proper error handling
- ✅ Fixed connection selection state management

### 🚀 Performance Improvements

- Bounded packet buffer to prevent memory growth
- O(1) connection lookup using dictionary
- Minimal packet processing (extract only needed fields)
- Efficient JSON serialization
- Client-side pagination (ready for large datasets)

### 📦 Dependencies

#### Backend (Python 3.8+)
```
scapy==2.5.0
pyroute2==0.7.12
```

#### Frontend (Node 14+)
```
react==18.2.0
react-dom==18.2.0
react-scripts==5.0.1
```

### 🔄 API Changes

#### Endpoints
- **GET /api/traffic** - Returns packets and connections
  - Response: `{ packets: [], connections: {} }`
  - CORS headers included
  - No authentication required (localhost only)

#### Data Models
- **Packet**: 14 fields (timestamp, IPs, ports, flags, seq/ack, window)
- **Connection**: 17 fields (4-tuple, state, bytes, RTT, etc.)

### 🧪 Testing

#### Test Scripts Included
- `tcp_test_server.py` - Simple TCP echo server
- `tcp_test_client.py` - TCP client for testing
- `test_tcp_connection.sh` - Long-lived connection script

#### Tested Scenarios
- ✅ Loopback traffic (interface: `lo`)
- ✅ Internet traffic (interface: `eth0`)
- ✅ HTTPS connections (port 443)
- ✅ Large downloads (window scaling)
- ✅ Connection establishment (3-way handshake)
- ✅ Connection teardown (FIN handshake)

### 📝 Configuration

#### Configurable Parameters
- Network interface (default: `eth0`)
- Packet buffer size (default: 1000)
- Backend port (default: 50052)
- Frontend polling interval (default: 1000ms)

### 🔐 Security Notes

- **Requires root** for packet capture
- **Local-only API** (binds to 127.0.0.1)
- **No authentication** - designed for development/testing
- **Privacy**: Can see all traffic on monitored interface

### 🎯 Known Limitations

1. **Platform**: Linux only (uses `/proc/net/tcp`)
2. **Scale**: Optimized for <1000 packets/sec
3. **History**: No persistent storage (in-memory only)
4. **Filtering**: No UI-based filtering yet
5. **IPv6**: Limited support (basic functionality only)

### 🔮 Future Enhancements

#### Planned for v1.1
- [ ] WebSocket streaming (replace HTTP polling)
- [ ] Packet filtering by IP/port/flags
- [ ] Export captured data to PCAP
- [ ] Connection duration tracking

#### Planned for v2.0
- [ ] eBPF integration for kernel-level capture
- [ ] Historical data storage (SQLite/TimescaleDB)
- [ ] Time-series RTT graphs
- [ ] Congestion window visualization

#### Planned for v3.0
- [ ] Multi-host distributed monitoring
- [ ] ML-based anomaly detection
- [ ] Advanced filtering DSL
- [ ] Performance profiling tools

### 📊 Metrics

#### Code Statistics
- **Total Lines**: ~1,600
  - Backend: ~800 lines (3 files)
  - Frontend: ~535 lines (2 files)
  - Tests: ~200 lines
  - Documentation: ~3,000 lines

#### Documentation Coverage
- 6 major documentation files
- 20+ code examples
- 10+ troubleshooting scenarios
- Complete API reference

### 🙏 Acknowledgments

- **Scapy**: Packet manipulation library
- **React**: Frontend framework
- **Linux Kernel**: `/proc/net/tcp` interface
- **Community**: Testing and feedback

### 📥 Installation

```bash
git clone https://github.com/emmanuelscaria/tcp-viewer.git
cd tcp-viewer

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install

# Run
# Terminal 1: cd backend && sudo venv/bin/python3 server.py
# Terminal 2: cd frontend && npm start
```

### 🔗 Links

- **Repository**: https://github.com/emmanuelscaria/tcp-viewer
- **Documentation**: See DOCUMENTATION_INDEX.md
- **Issues**: GitHub Issues tab
- **License**: MIT

---

## [0.9.0] - 2025-12-13

### Development Phase (Pre-release)

- Initial project structure
- gRPC prototyping (later replaced with HTTP)
- Basic packet capture implementation
- React UI scaffolding

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) principles.

### Types of Changes
- `Added` for new features
- `Changed` for changes in existing functionality
- `Deprecated` for soon-to-be removed features
- `Removed` for now removed features
- `Fixed` for any bug fixes
- `Security` in case of vulnerabilities

---

**Maintained by**: Emmanuel Scaria  
**Last Updated**: December 14, 2025
