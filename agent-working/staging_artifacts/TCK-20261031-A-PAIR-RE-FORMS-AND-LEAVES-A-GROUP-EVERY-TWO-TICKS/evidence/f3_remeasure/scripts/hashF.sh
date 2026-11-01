#!/bin/bash
# 3 pinned FULL 2000t s42 hash runs on f6cd0e057, one at a time, cores 4-5; expected 66101cd32511 (crowded_frontier) a872018bf494 (frontier_living_world) ae41db137ac7 (urban_political)
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_hashF; mkdir -p $O; sha=f6cd0e057
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=gov
for pair in crowded_frontier:66101cd32511 frontier_living_world:a872018bf494 urban_political:ae41db137ac7; do w=${pair%%:*}; exp=${pair#*:}
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "HASHF_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  TIM_OUT=$O/$w.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 2000 > $O/$w.stdout 2>&1
  rc=$?; h=$($PY -c "import json;print(json.load(open('$O/$w.json'))['state_hash'][:12])" 2>/dev/null)
  echo "HASHF $w rc=$rc wall_s=$(( $(date +%s)-ST )) hash=$h expected=$exp $([ "$h" = $exp ] && echo EQUAL || echo MOVED)"
  [ "$h" = $exp ] || { echo "HASHF_STOP moved"; exit 4; }
done; echo HASHF_DONE
