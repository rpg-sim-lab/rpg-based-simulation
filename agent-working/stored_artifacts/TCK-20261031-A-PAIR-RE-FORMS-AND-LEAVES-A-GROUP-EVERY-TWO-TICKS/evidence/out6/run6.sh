#!/bin/bash
# 6 unprofiled runs (NOPROF=1, profile_run.py with counting fields), s42 2000t, audit_mode, PYTHONHASHSEED=0, cores 4-5, sequential. Stops at 35 min own wall or on hash mismatch.
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out6; START=$(date +%s)
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
declare -A EXP=( [crowded_frontier_6fdfdf555]=3ffb7e977126 [crowded_frontier_edb638b6a]=59e493606658 [frontier_living_world_6fdfdf555]=93a1944fe116 [frontier_living_world_edb638b6a]=85fcc03d4ee9 [urban_political_6fdfdf555]=327f8e441f2b [urban_political_edb638b6a]=14fc468be808 )
for w in crowded_frontier frontier_living_world urban_political; do for sha in 6fdfdf555 edb638b6a; do
  lab=${w}_$sha
  [ $(( $(date +%s)-START )) -ge 2100 ] && { echo "RUN6_STOP 35 min wall before $lab"; exit 6; }
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "RUN6_STOP memory $m before $lab"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s); echo "RUN6_START $lab mem_kB=$m at=$(date +%H:%M:%S)"
  NOPROF=1 PROBE_OUT=$O/$lab.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/profile_run.py $w 42 2000 > $O/$lab.stdout 2>&1
  rc=$?; h=$($PY -c "import json;print(json.loads(open('$O/$lab.jsonl').read().splitlines()[-1])['state_hash'][:12])" 2>/dev/null)
  mf=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
  echo "RUN6_DONE $lab rc=$rc wall_s=$(( $(date +%s)-ST )) hash=$h expected=${EXP[$lab]} $([ "$h" = "${EXP[$lab]}" ] && echo MATCH || echo MISMATCH) mem_start_kB=$m mem_end_kB=$mf at=$(date +%H:%M:%S)"
  [ $rc -eq 0 ] && [ "$h" = "${EXP[$lab]}" ] || { echo "RUN6_STOP rc/hash at $lab"; exit 5; }
done; done
echo RUN6_ALL_DONE
