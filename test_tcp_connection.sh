#!/bin/bash
echo "Creating test TCP connection..."
echo "This will make an HTTP request to generate TCP traffic"

# Make a request to a remote server
curl -s http://example.com/ > /dev/null &
sleep 2
curl -s http://www.google.com/ > /dev/null &
sleep 2

echo "Test connections created. Check the TCP Viewer UI!"
echo "The connections should appear in the Active Connections table."
