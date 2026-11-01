#!/bin/bash
# step (a): 3 runs (one per world), s42, 2000 ticks, non-audit pinned FULL (PinnedNormalGovernor), ConcurrentExecutionAdapter, timing_run.py with VISITS=1, on the step-(a) tree; hash must equal the churn tree's
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_stepa; mkdir -p $O; sha=a6902557b
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=gov VISITS=1
declare -A EXP=( [crowded_frontier]=66101cd32511 [frontier_living_world]=a872018bf494 [urban_political]=ae41db137ac7 )
for w in crowded_frontier frontier_living_world urban_political; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "STEPA_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  TIM_OUT=$O/$w.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 2000 > $O/$w.stdout 2>&1
  rc=$?; h=$($PY -c "import json;print(json.load(open('$O/$w.json'))['state_hash'][:12])" 2>/dev/null)
  echo "STEPA $w rc=$rc wall_s=$(( $(date +%s)-ST )) hash=$h expected=${EXP[$w]} $([ "$h" = "${EXP[$w]}" ] && echo MATCH || echo MISMATCH) mem_kB=$m"
done; echo STEPA_DONE
