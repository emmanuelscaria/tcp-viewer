# TCP Viewer - Frontend

React.js frontend for TCP traffic visualization.

## Setup

**Note:** This requires Node.js and npm to be installed. If not available, install with:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm
```

Then install dependencies:
```bash
npm install
```

## Running

Start the development server:
```bash
npm start
```

The app will open at `http://localhost:3000`

## Architecture

- **App.js**: Main component with split-panel layout
- **index.js**: React entry point
- **App.css**: Styling for dark theme UI

## Current Features (Phase 1)

- ✅ Split-panel dashboard layout
- ✅ Active connections table
- ✅ Live packet stream display
- ✅ Connection detail view with tcpcb parameters
- ✅ State-based color coding
- ⚠️ Simulated data (replace with gRPC-Web client)

## Integration with Backend

To connect to the Python gRPC backend, you'll need:

1. **Envoy Proxy** for gRPC-Web (gRPC doesn't work directly in browsers)
2. **Generated JavaScript gRPC client** from the `.proto` file

### Setting up gRPC-Web (Phase 1.5)

Install protoc plugin:
```bash
npm install -g grpc-web
```

Generate JavaScript client stubs:
```bash
protoc -I=../proto tcp_monitor.proto \
  --js_out=import_style=commonjs:./src \
  --grpc-web_out=import_style=commonjs,mode=grpcwebtext:./src
```

Configure Envoy proxy to bridge gRPC to gRPC-Web (example config in `/envoy` directory).

## Next Steps

- Replace simulated data with real gRPC-Web client
- Add filtering controls
- Implement RTT time-series graphs (Phase 3)
- Add virtualized scrolling for performance (react-window)
