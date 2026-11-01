#!/bin/bash
# C: 15 paired audit runs, 3 worlds x s42-46 x 2000t, base 30307228c (F3 on main) vs arm effd2e8fc (churn fix merged on it); m15.py (NOPROF=1), PYTHONHASHSEED=0, cores 4-5, sequential, resumable,
# alternate order per pair, MemAvailable >= 3 GB; STOP at world end on tier-1 (7), lodged/just-out-of-bed extra victim (9), hard law not {} (10); lag > 0 per pair (8)
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out15F; mkdir -p $O; B=30307228c; A=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
START=$(date +%s); n=0
for w in crowded_frontier frontier_living_world urban_political; do for seed in 42 43 44 45 46; do
  n=$((n+1)); if [ $((n%2)) = 1 ]; then order="base:$B branch:$A"; else order="branch:$A base:$B"; fi
  for spec in $order; do lab=${spec%%:*}; sha=${spec#*:}; key=${w}_s${seed}_$lab
    [ -f $O/$key.done ] && continue
    [ $(( $(date +%s)-START )) -ge 14400 ] && { echo "RUN15F_STOP 4h wall before $key"; exit 6; }
    for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
    [ "$m" -ge 3145728 ] || { echo "RUN15F_STOP memory $m before $key"; exit 3; }
    cd $T/trees/$sha; ST=$(date +%s); echo "RUN15F_START $key mem_kB=$m at=$(date +%H:%M:%S)"
    NOPROF=1 PROBE_OUT=$O/$key.jsonl M15_OUT=$O/$key.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/m15.py $w $seed 2000 > $O/$key.stdout 2>&1
    rc=$?
    echo "RUN15F_DONE $key rc=$rc wall_s=$(( $(date +%s)-ST )) at=$(date +%H:%M:%S)"
    [ $rc -eq 0 ] && [ -f $O/$key.json ] && echo ok > $O/$key.done || { echo "RUN15F_STOP rc=$rc at $key"; exit 5; }
  done
  $PY $T/pair_check.py $O/${w}_s${seed}_base.json $O/${w}_s${seed}_branch.json; prc=$?; [ $prc -eq 8 ] && { echo "RUN15F_STOP lag > 0 at ${w}_s${seed}"; exit 8; }; echo "PAIR_DONE ${w}_s${seed} total_wall_s=$(( $(date +%s)-START ))"
done
  $PY $T/worldF.py $w $O; wrc=$?
  echo "WORLD_DONE $w check_rc=$wrc total_wall_s=$(( $(date +%s)-START ))"
  [ $wrc -eq 0 ] || { echo "RUN15F_STOP world end rc=$wrc in $w (7 tier-1, 9 lodged victim, 10 hard law)"; exit 7; }
done
echo RUN15F_ALL_DONE
