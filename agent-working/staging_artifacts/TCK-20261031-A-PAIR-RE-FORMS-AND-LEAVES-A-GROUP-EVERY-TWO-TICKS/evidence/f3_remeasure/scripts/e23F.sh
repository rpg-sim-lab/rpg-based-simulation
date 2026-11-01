#!/bin/bash
# job: e23 pair: urban_political s42, WATCH/TENT 23,24 (+ every entity within Euclid 10 of e23 at the call), window t1630-1690, both arms, run to 1700; control window t1630-1640 counts the role marks over ALL entities
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_e23; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
for sha in effd2e8fc 30307228c; do
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "E23_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  WATCH=23,24 TENT=23,24 NEAR=23 TWIN=1630,1690 CTRLWIN=1630,1640 TR_OUT=$O/u42_$sha.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_e23.py urban_political 42 1700 0 > $O/u42_$sha.stdout 2>&1
  echo "E23 $sha rc=$? wall_s=$(( $(date +%s)-ST )) $(tail -1 $O/u42_$sha.stdout) mem_start_kB=$m"
done; echo E23_DONE
