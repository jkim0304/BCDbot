#!/bin/bash
make build
sudo ./bcdserver > server.log &
python3 bot.py &
disown -a