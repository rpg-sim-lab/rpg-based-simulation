#!/bin/bash
# positive control for the F3 lodger row: base tree 30307228c, s42 600t per world; m15.py (instrumented) vs timing_run.py (uninstrumented) hashes must match; lodger counters non-zero somewhere
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_ctlL; mkdir -p $O; sha=30307228c
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0 PIN=gov
cd $T/trees/$sha
for w in crowded_frontier frontier_living_world urban_political; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "CTLL_STOP memory $m"; exit 3; }
  NOPROF=1 PROBE_OUT=$O/${w}_m15.jsonl M15_OUT=$O/${w}_m15.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/m15.py $w 42 600 > $O/${w}_m15.stdout 2>&1; r1=$?
  TIM_OUT=$O/${w}_tim.json PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/timing_run.py $w 42 600 > $O/${w}_tim.stdout 2>&1; r2=$?
  $PY - <<PY2
import json
a=json.load(open("$O/${w}_m15.json")); b=json.load(open("$O/${w}_tim.json")); L=a.get("lodged",{})
print("CTLL $w rc=$r1/$r2 m15_hash=%s tim_hash=%s %s | field_found=%s lodger_ticks=%s enters=%d leaves=%d group_decision_lodged=%s over %s ticks" % (a["state_hash"][:12], b["state_hash"][:12], "MATCH" if a["state_hash"]==b["state_hash"] else "MISMATCH", L.get("field_found"), L.get("lodger_ticks"), len(L.get("enters",[])), len(L.get("leaves",[])), L.get("group_decision_lodged"), L.get("group_decision_ticks")))
PY2
done; echo CTLL_DONE
