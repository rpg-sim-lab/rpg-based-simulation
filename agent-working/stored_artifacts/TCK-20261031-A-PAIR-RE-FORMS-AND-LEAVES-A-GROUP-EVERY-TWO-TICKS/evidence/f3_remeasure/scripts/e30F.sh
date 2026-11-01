#!/bin/bash
# job 1: e30 tactical trace, frontier s43, arm effd2e8fc, window t1395-1401, watching 12, 30, 6; run to 1440 so the death list and hash match trace_lodge's arm run (hash 5a9e2a8746b3)
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_e30; mkdir -p $O; sha=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "E30_STOP memory $m"; exit 3; }
cd $T/trees/$sha; ST=$(date +%s)
WATCH=12,30,6 TENT=12,30,6 TWIN=1395,1401 TR_OUT=$O/f43_$sha.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_e30.py frontier_living_world 43 1440 0 > $O/f43.stdout 2>&1; rc=$?
echo "E30 rc=$rc wall_s=$(( $(date +%s)-ST )) $(tail -1 $O/f43.stdout) expected_hash=5a9e2a8746b3 mem_start_kB=$m"; echo E30_DONE
