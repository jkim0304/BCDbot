#!/bin/bash
python3 bot.py & 
cd gui
python3 bcdserver.py & > bcdserver.log 
disown -a

