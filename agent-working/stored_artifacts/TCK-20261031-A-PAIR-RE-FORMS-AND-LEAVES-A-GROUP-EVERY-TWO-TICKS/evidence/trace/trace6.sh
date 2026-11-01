#!/bin/bash
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_trace; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
START=$(date +%s)
for sha in ${SHAS:-edb638b6a 6fdfdf555}; do
  [ $(( $(date +%s)-START )) -ge 780 ] && { echo "TRACE_STOP time before $sha"; exit 6; }
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "TRACE_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  PAIR=${PAIR:-19,33} WIN=${WIN:-90,116} TRACE_OUT=$O/${TAG:-crowded}_$sha.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_contract.py crowded_frontier 42 ${NT:-117} > $O/${TAG:-crowded}_$sha.stdout 2>&1
  echo "TRACE_DONE $sha rc=$? wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
done; echo TRACE_ALL_DONE
