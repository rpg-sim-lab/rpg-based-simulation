#!/bin/bash
# job 2: m15_dec.py on the arm effd2e8fc, frontier s43 s44 s45, 2000t, audit, cores 4-5, one at a time; each state_hash must equal the unprobed arm run in out15F
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_decF; mkdir -p $O; sha=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
cd $T/trees/$sha
for seed in 42; do key=urban_political_s${seed}_branch
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "DECU_STOP memory $m"; exit 3; }
  sw=$(awk '/SwapTotal/{t=$2}/SwapFree/{f=$2}END{print t-f}' /proc/meminfo); ST=$(date +%s)
  NOPROF=1 PROBE_OUT=$O/$key.jsonl M15_OUT=$O/$key.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/m15_dec.py urban_political $seed 2000 > $O/$key.stdout 2>&1; rc=$?
  h=$($PY -c "import json;print(json.load(open('$O/$key.json'))['state_hash'])" 2>/dev/null); e=$($PY -c "import json;print(json.load(open('$T/out15F/$key.json'))['state_hash'])")
  echo "DECU $key rc=$rc wall_s=$(( $(date +%s)-ST )) hash=${h:0:12} unprobed=${e:0:12} $([ "$h" = "$e" ] && echo EQUAL || echo MOVED) mem_start_kB=$m swap_used_kB=$sw"
  [ "$h" = "$e" ] || { echo "DECU_STOP hash moved"; exit 4; }
done; echo DECU_DONE
