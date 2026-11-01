#!/bin/bash
# samples swap-in/out counters and MemAvailable every 5 s: epoch pswpin pswpout memavail_kB swapfree_kB
while true; do
  echo "$(date +%s) $(awk '/^pswpin/{a=$2} /^pswpout/{b=$2} END{printf "%s %s",a,b}' /proc/vmstat) $(awk '/MemAvailable/{m=$2} /SwapFree/{s=$2} END{print m, s}' /proc/meminfo)"
  sleep 5
done >> "$1"
