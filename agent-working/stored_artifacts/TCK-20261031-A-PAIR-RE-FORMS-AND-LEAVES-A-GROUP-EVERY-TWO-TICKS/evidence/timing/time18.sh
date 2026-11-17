#!/bin/bash
# 18 non-audit timing runs: crowded_frontier, frontier_living_world, urban_political x s42, 3 reps x {base c9b9a50f4, branch 59f0e78bd}, rep-major (rep 1 = 6 runs), order flipped in rep 2,
# timing_run.py (PIN env = governor pin mode), cores 4-5, one at a time, MemAvailable >= 3 GB before each, stop at 90 min own wall, resumable (.done), swap sampler for the whole set.
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_time; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=${PIN:-gov}
START=$(date +%s); [ -f $O/swap.log ] || : > $O/swap.log
$T/swap_sampler.sh $O/swap.log & SP=$!; trap "kill $SP 2>/dev/null" EXIT
for rep in 1 2 3; do for w in crowded_frontier frontier_living_world urban_political; do
  if [ $rep = 2 ]; then order="branch:59f0e78bd base:c9b9a50f4"; else order="base:c9b9a50f4 branch:59f0e78bd"; fi
  for spec in $order; do lab=${spec%%:*}; sha=${spec#*:}; key=${w}_r${rep}_$lab
    [ -f $O/$key.done ] && continue
    [ $(( $(date +%s)-START )) -ge 5400 ] && { echo "TIME_STOP 90 min wall before $key"; exit 6; }
    for i in 1 2 3 4 5 6 7 8 9 10; do m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] && break; sleep 60; done
    [ "$m" -ge 3145728 ] || { echo "TIME_STOP memory $m before $key"; exit 3; }
    cd $T/trees/$sha; ST=$(date +%s); echo "TIME_START $key mem_kB=$m at=$(date +%H:%M:%S) epoch=$ST"
    TIM_OUT=$O/$key.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 2000 > $O/$key.stdout 2>&1
    rc=$?; EN=$(date +%s)
    echo "TIME_DONE $key rc=$rc wall_s=$(( EN-ST )) epoch_start=$ST epoch_end=$EN at=$(date +%H:%M:%S)"
    [ $rc -eq 0 ] && [ -f $O/$key.json ] && echo "$ST $EN" > $O/$key.done || { echo "TIME_STOP rc=$rc at $key"; exit 5; }
  done
  [ $w = urban_political ] && echo "REP_WORLD_DONE rep $rep total_wall_s=$(( $(date +%s)-START ))"
done; echo "REP_DONE $rep total_wall_s=$(( $(date +%s)-START ))"; done
echo TIME_ALL_DONE
