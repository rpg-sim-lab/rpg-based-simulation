#!/bin/bash
# occupancy/retreat probe: urban s42 arm effd2e8fc, run to t1690 (death list must equal C's up to 1690)
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_occ; mkdir -p $O; sha=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "OCC_STOP memory $m"; exit 3; }
sw=$(awk '/SwapTotal/{t=$2}/SwapFree/{f=$2}END{print t-f}' /proc/meminfo); cd $T/trees/$sha; ST=$(date +%s)
TR_OUT=$O/u42.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_occ.py urban_political 42 1690 > $O/u42.stdout 2>&1
echo "OCC rc=$? wall_s=$(( $(date +%s)-ST )) $(tail -1 $O/u42.stdout) mem_start_kB=$m swap_used_kB=$sw"; echo OCC_DONE
