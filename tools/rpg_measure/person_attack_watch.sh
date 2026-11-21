#!/bin/bash
# Usage: person_attack_watch.sh <logfile>.  Env (never the command line): PAT (a regex of the child command lines), THRESHOLD_KIB (default 2988000 = 2.85 GiB), WAIT_S (default 60).
# Waits up to WAIT_S for a process matching PAT, logs "WATCHER NO CHILD" and exits 2 if none appears; then, while one exists, kills them all when their summed RSS passes THRESHOLD_KIB.
LOG=$1
PAT=${PAT:?PAT must be set in the environment}
LIMIT=${THRESHOLD_KIB:-2988000}
WAIT_S=${WAIT_S:-60}
waited=0
until pgrep -f -- "$PAT" >/dev/null; do
  if [ "$waited" -ge "$WAIT_S" ]; then echo "WATCHER NO CHILD after ${WAIT_S}s $(date +%T)" >> "$LOG"; exit 2; fi
  sleep 1; waited=$((waited+1))
done
echo "WATCHER SAW CHILD after ${waited}s $(date +%T)" >> "$LOG"
while pgrep -f -- "$PAT" >/dev/null; do
  rss=$(ps -eo rss,args | grep -E -- "$PAT" | grep -v grep | awk '{s+=$1} END{print s+0}')
  if [ "$rss" -gt "$LIMIT" ]; then echo "WATCHER KILL rss_kib=$rss limit_kib=$LIMIT $(date +%T)" >> "$LOG"; pkill -f -- "$PAT"; fi
  sleep 1
done
echo "WATCHER END $(date +%T)" >> "$LOG"
