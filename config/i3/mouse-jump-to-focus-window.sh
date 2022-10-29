#!/bin/bash

# from https://github.com/i3/i3/issues/2971#issuecomment-756322809

XDT=/usr/bin/xdotool

WINDOW=`$XDT getwindowfocus`

# this brings in variables WIDTH and HEIGHT
eval `xdotool getwindowgeometry --shell $WINDOW`

if [ $HEIGHT -gt 100 ]
then
  TX=`expr $WIDTH / 2`
  TY=`expr $HEIGHT / 2`

  $XDT mousemove -window $WINDOW $TX $TY
else
  rect=$(i3-msg -t get_workspaces | jq -r '.[] | select(.focused==true).rect')

  x=$(jq -r '.x' <<< $rect)
  y=$(jq -r '.y' <<< $rect)
  w=$(jq -r '.width' <<< $rect)
  h=$(jq -r '.height' <<< $rect)
  TX=`expr $x + $w / 2`
  TY=`expr $y + $h / 2`
  $XDT mousemove -window $WINDOW $TX $TY
fi
