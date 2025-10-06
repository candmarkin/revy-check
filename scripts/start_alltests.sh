#!/bin/bash

xset -dpms
xset s off
xset s noblank

/usr/bin/xinit /usr/bin/python3 /home/revy/revy-check/main.py -- :0 -nolisten tcp vt1
