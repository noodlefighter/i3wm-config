#!/bin/bash

cd ~/nutstore/BG

while :
do
  killall swaybg
  swaybg -i $(ls |sort -R |tail -1) --mode fill &
	sleep 600
done
