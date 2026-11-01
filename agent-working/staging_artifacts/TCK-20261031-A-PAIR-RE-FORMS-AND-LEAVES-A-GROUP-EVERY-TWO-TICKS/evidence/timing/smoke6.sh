#!/bin/bash
# 6 smokes: 3 worlds x 2 trees, s42, 600 ticks, timing_run.py with PIN=gov (PinnedNormalGovernor, executor default), cores 4-5, one at a time
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_time_smoke; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=gov
for w in crowded_frontier frontier_living_world urban_political; do for spec in base:c9b9a50f4 branch:59f0e78bd; do lab=${spec%%:*}; sha=${spec#*:}
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "SMOKE_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  TIM_OUT=$O/${w}_$lab.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 600 > $O/${w}_$lab.stdout 2>&1
  echo "SMOKE $w $lab rc=$? wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
done; done; echo SMOKE_DONE
