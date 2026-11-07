#!/bin/bash
# Tier-2 traces, arm effd2e8fc only: for each (world, seed) the extra COMBAT victims (arm-only, from out15F), window = death-60 .. death+2 per victim; traced evaluate_entity_intent calls for the victim and every entity within Euclid 10 of it (the killer included), marks incl. 5.2 bracketing; lodging leave/claim rows; control = death list equals C's
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_t2; mkdir -p $O; sha=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
for spec in crowded_frontier:43 frontier_living_world:45 urban_political:44; do w=${spec%%:*}; seed=${spec#*:}
  read WINS NT <<< $($PY - <<PY2
import json
a=json.load(open("$T/out15F/${w}_s${seed}_branch.json")); b=json.load(open("$T/out15F/${w}_s${seed}_base.json"))
bs={(x[1],x[2]) for x in b["deaths"]}; ex=[x for x in a["deaths"] if x[2]=="COMBAT" and (x[1],x[2]) not in bs]
print(";".join("%d-%d:%d"%(max(1,x[0]-60),x[0]+2,x[1]) for x in ex), max(x[0] for x in ex)+6)
PY2
)
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "T2_STOP memory $m before $w"; exit 3; }
  sw=$(awk '/SwapTotal/{t=$2}/SwapFree/{f=$2}END{print t-f}' /proc/meminfo)
  cd $T/trees/$sha; ST=$(date +%s)
  WINS="$WINS" CTRLWIN=0,-1 TR_OUT=$O/${w}_s${seed}.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_t2.py $w $seed $NT 0 > $O/${w}_s${seed}.stdout 2>&1; rc=$?
  echo "T2 $w s$seed rc=$rc wall_s=$(( $(date +%s)-ST )) ticks=$NT wins=$WINS $(tail -1 $O/${w}_s${seed}.stdout) mem_start_kB=$m swap_used_kB=$sw"
done; echo T2_DONE
