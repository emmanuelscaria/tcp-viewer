#!/bin/bash
pkill -f server 2>/dev/null
sleep 1
sudo venv/bin/python3 server.py
