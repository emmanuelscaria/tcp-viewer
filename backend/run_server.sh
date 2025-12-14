#!/bin/bash
pkill -f server_with_http.py 2>/dev/null
sleep 1
venv/bin/python3 server_with_http.py
