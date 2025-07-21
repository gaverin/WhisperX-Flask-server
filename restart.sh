#!/bin/sh
sleep 5
pid=$(cat /tmp/stt-server.pid)
kill "$pid"
python3 -W ignore stt_server.py