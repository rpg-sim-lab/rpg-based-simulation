#!/bin/bash
# 15 paired runs: 3 worlds x s42-46, base c9b9a50f4 vs branch 9e3b07c22, m15.py (NOPROF=1), audit_mode, PYTHONHASHSEED=0, cores 4-5, sequential, resumable (.done markers),
# alternating which tree goes first per pair, MemAvailable >= 3 GB before each run, stop at 4 h own wall, no stop per pair; STOP only if a world's Tier-1 death bar fires (world_check.py).
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out15; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
START=$(date +%s); n=0
for w in crowded_frontier frontier_living_world urban_political; do for seed in 42 43 44 45 46; do
  n=$((n+1)); if [ $((n%2)) = 1 ]; then order="base:c9b9a50f4 branch:9e3b07c22"; else order="branch:9e3b07c22 base:c9b9a50f4"; fi
  for spec in $order; do lab=${spec%%:*}; sha=${spec#*:}; key=${w}_s${seed}_$lab
    [ -f $O/$key.done ] && continue
    [ $(( $(date +%s)-START )) -ge 14400 ] && { echo "RUN15_STOP 4h wall before $key"; exit 6; }
    for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
    [ "$m" -ge 3145728 ] || { echo "RUN15_STOP memory $m before $key"; exit 3; }
    cd $T/trees/$sha; ST=$(date +%s); echo "RUN15_START $key mem_kB=$m at=$(date +%H:%M:%S)"
    NOPROF=1 PROBE_OUT=$O/$key.jsonl M15_OUT=$O/$key.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/m15.py $w $seed 2000 > $O/$key.stdout 2>&1
    rc=$?; mf=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    echo "RUN15_DONE $key rc=$rc wall_s=$(( $(date +%s)-ST )) mem_start_kB=$m mem_end_kB=$mf at=$(date +%H:%M:%S)"
    [ $rc -eq 0 ] && [ -f $O/$key.json ] && echo ok > $O/$key.done || { echo "RUN15_STOP rc=$rc at $key"; exit 5; }
  done
  $PY $T/pair_check.py $O/${w}_s${seed}_base.json $O/${w}_s${seed}_branch.json; echo "PAIR_DONE ${w}_s${seed} at=$(date +%H:%M:%S) total_wall_s=$(( $(date +%s)-START ))"
done
  $PY $T/world_check.py $w $O; wrc=$?
  echo "WORLD_DONE $w check_rc=$wrc at=$(date +%H:%M:%S) total_wall_s=$(( $(date +%s)-START ))"
  [ $wrc -eq 0 ] || { echo "RUN15_STOP tier-1 death rise in $w"; exit 7; }
done
echo RUN15_ALL_DONE
