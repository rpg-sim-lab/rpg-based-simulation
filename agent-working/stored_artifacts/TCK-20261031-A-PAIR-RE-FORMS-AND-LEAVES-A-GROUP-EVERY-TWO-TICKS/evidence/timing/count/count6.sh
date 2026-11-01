#!/bin/bash
# 6 work-count runs: 3 worlds x 2 trees, s42, 2000 ticks, non-audit pinned FULL (PinnedNormalGovernor), ConcurrentExecutionAdapter, same wrapper as the 18 (timing_run.py, PIN=gov); stop at 35 min; hash must equal the 18's
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_count; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=gov
START=$(date +%s)
declare -A EXP=( [crowded_frontier_base]=3ffb7e977126 [crowded_frontier_branch]=66101cd32511 [frontier_living_world_base]=93a1944fe116 [frontier_living_world_branch]=a872018bf494 [urban_political_base]=327f8e441f2b [urban_political_branch]=ae41db137ac7 )
for w in crowded_frontier frontier_living_world urban_political; do for spec in base:c9b9a50f4 branch:59f0e78bd; do lab=${spec%%:*}; sha=${spec#*:}; key=${w}_$lab
  [ $(( $(date +%s)-START )) -ge 2100 ] && { echo "COUNT_STOP 35 min before $key"; exit 6; }
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "COUNT_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  TIM_OUT=$O/$key.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 2000 > $O/$key.stdout 2>&1
  rc=$?; h=$($PY -c "import json;print(json.load(open('$O/$key.json'))['state_hash'][:12])" 2>/dev/null)
  echo "COUNT $key rc=$rc wall_s=$(( $(date +%s)-ST )) hash=$h expected=${EXP[$key]} $([ "$h" = "${EXP[$key]}" ] && echo MATCH || echo MISMATCH) mem_kB=$m"
done; done; echo COUNT_DONE
