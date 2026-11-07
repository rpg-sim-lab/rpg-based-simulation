#!/bin/bash
# 3 proof runs on 59f0e78bd, s42 per world, m15.py wrapper, expected hashes equal the fc22ae71f runs
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_proof; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
declare -A EXP=( [crowded_frontier]=66101cd32511 [frontier_living_world]=a872018bf494 [urban_political]=ae41db137ac7 )
sha=59f0e78bd
for w in crowded_frontier frontier_living_world urban_political; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "PROOF_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  NOPROF=1 PROBE_OUT=$O/${w}_s42.jsonl M15_OUT=$O/${w}_s42.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/m15.py $w 42 2000 > $O/${w}_s42.stdout 2>&1
  rc=$?; h=$($PY -c "import json;print(json.load(open('$O/${w}_s42.json'))['state_hash'][:12])" 2>/dev/null)
  echo "PROOF $w rc=$rc wall_s=$(( $(date +%s)-ST )) hash=$h expected=${EXP[$w]} $([ "$h" = "${EXP[$w]}" ] && echo MATCH || echo MISMATCH) mem_kB=$m"
  [ "$h" = "${EXP[$w]}" ] || { echo "PROOF_STOP hash mismatch at $w"; exit 5; }
done; echo PROOF_ALL_MATCH
