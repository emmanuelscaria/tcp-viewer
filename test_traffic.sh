#!/bin/bash

echo "==========================================="
echo "Generating TCP Traffic on eth0"
echo "==========================================="
echo ""

# Function to make HTTP requests
test_http() {
    echo "Testing HTTP connections..."
    curl -s http://www.google.com > /dev/null &
    curl -s http://www.github.com > /dev/null &
    curl -s http://www.ubuntu.com > /dev/null &
    sleep 1
}

# Function to test HTTPS connections
test_https() {
    echo "Testing HTTPS connections..."
    curl -s https://www.google.com > /dev/null &
    curl -s https://www.github.com > /dev/null &
    curl -s https://www.cloudflare.com > /dev/null &
    sleep 1
}

# Function to download a file
test_download() {
    echo "Testing file download..."
    curl -s -o /tmp/test_download.html https://www.example.com &
    sleep 2
}

# Run multiple rounds of tests
echo "Round 1: HTTP connections"
test_http

echo "Round 2: HTTPS connections"
test_https

echo "Round 3: Mixed traffic"
test_http &
test_https &
wait

echo "Round 4: Download test"
test_download

echo ""
echo "==========================================="
echo "Traffic generation complete!"
echo "Check your TCP Viewer for captured packets"
echo "==========================================="

# Clean up
rm -f /tmp/test_download.html
