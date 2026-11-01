#!/bin/bash
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_trace15; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
for spec in "base:c9b9a50f4" "branch:9e3b07c22"; do lab=${spec%%:*}; sha=${spec#*:}
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  TR_OUT=$O/$lab.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_pair.py crowded_frontier 42 2000 520 2>&1 | grep -E "TRACE_OK|Error|Traceback" | head -3
  echo "TRACE15 $lab wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
done; echo TRACE15_DONE
