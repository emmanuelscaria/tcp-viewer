#!/bin/bash
# Generate Python gRPC stubs from proto file

python3 -m grpc_tools.protoc \
  -I../proto \
  --python_out=. \
  --grpc_python_out=. \
  ../proto/tcp_monitor.proto

echo "Generated gRPC Python stubs successfully!"
