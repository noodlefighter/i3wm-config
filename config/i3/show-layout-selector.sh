#!/bin/bash

 i3-instant-layout --list | rofi -dmenu -p "选择平铺模式:" | i3-instant-layout -
