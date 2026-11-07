#!/bin/bash
# NOT RUN: trace pair for the C lodger STOP: frontier_living_world s43, entities 12 and 6, window t1360-1433 (run to 1440), base 30307228c vs arm effd2e8fc, audit, pinned hash seed, cores 4-5, one at a time
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_trace_lodge; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
for sha in effd2e8fc 30307228c; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "TRL_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  WATCH=12,6 TWIN=1360,1433 TR_OUT=$O/f43_$sha.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_lodge.py frontier_living_world 43 1440 0 > $O/f43_$sha.stdout 2>&1
  echo "TRL_DONE $sha rc=$? wall_s=$(( $(date +%s)-ST )) $(tail -1 $O/f43_$sha.stdout)"
done; echo TRL_ALL_DONE
