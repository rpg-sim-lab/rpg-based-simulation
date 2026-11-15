#!/bin/bash
# usage: run_cell.sh <label> <script> <args...>   (cwd = tree). Checks free >=3500, runs one process under a 1 s guard that kills at <1000 MB available.
D=/mnt/data2/rpg-measure/nobody-eats
label=$1; shift
A=$(free -m | awk '/^Mem:/{print $7}')
echo "$label start available=${A}MB $(date +%T)" >> $D/status.txt
if [ "$A" -lt 3500 ]; then echo "$label REFUSED available=$A" >> $D/status.txt; exit 3; fi
cd $D/tree
PYTHONHASHSEED=0 PYTHONPATH=. /mnt/data/scratch-deps-venv/bin/python "$@" > $D/$label.log 2>&1 &
P=$!
MIN=99999; PEAK=0
while kill -0 $P 2>/dev/null; do
  R=$(awk '/VmHWM/{print $2}' /proc/$P/status 2>/dev/null); [ -n "$R" ] && [ "$R" -gt "$PEAK" ] && PEAK=$R
  A=$(free -m | awk '/^Mem:/{print $7}'); [ "$A" -lt "$MIN" ] && MIN=$A
  if [ "$A" -lt 1000 ]; then kill -9 $P; echo "$label GUARD_KILL available=$A peak_rss_kb=$PEAK" >> $D/status.txt; exit 4; fi
  sleep 1
done
wait $P; rc=$?
echo "$label end rc=$rc min_available=${MIN}MB peak_rss_kb=$PEAK $(date +%T)" >> $D/status.txt
exit $rc
