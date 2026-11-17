#!/bin/bash
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; t=$T/trees/80a8a94a4; O=$T/out_D; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
cd $t
for hs in 0 1; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "D_STOP memory $m"; exit 3; }
  PYTHONHASHSEED=$hs PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/fullrows.py lifecycle_full_coverage_world 42 200 $O/seed$hs.jsonl > $O/seed$hs.log 2>&1; echo "D seed=$hs rc=$? $(tail -1 $O/seed$hs.log)"
done
cmp $O/seed0.jsonl $O/seed1.jsonl && echo "D_IDENTICAL $(wc -l < $O/seed0.jsonl) rows $(sha256sum < $O/seed0.jsonl | cut -c1-12)" || echo D_DIFFER
echo D_DONE
