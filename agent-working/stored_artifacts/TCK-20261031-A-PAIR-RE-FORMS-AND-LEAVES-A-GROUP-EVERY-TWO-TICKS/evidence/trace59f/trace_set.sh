#!/bin/bash
# usage: trace_set.sh <world> <seed> : base c9b9a50f4 and branch 59f0e78bd, trace_pair2.py, WATCH = every death id in either tree of that pair, hash detail to t520
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; w=$1; s=$2; O=$T/out_trace2/${w}_s$s; mkdir -p $O
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
WATCH=$($PY -c "
import json
ids=set()
for lab in ('base','branch'):
    ids|={x[1] for x in json.load(open('$T/out15/${w}_s${s}_%s.json'%lab))['deaths']}
print(','.join(map(str,sorted(ids))))")
echo "WATCH=$WATCH"
for spec in base:c9b9a50f4 branch:59f0e78bd; do lab=${spec%%:*}; sha=${spec#*:}
  m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "TRACE_STOP memory $m"; exit 3; }
  cd $T/trees/$sha; ST=$(date +%s)
  WATCH=$WATCH TR_OUT=$O/$lab.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_pair2.py $w $s 2000 520 2>&1 | grep -E "TRACE_OK|Error|Traceback" | head -3
  echo "TRACE2 $w s$s $lab wall_s=$(( $(date +%s)-ST )) mem_kB=$m"
done; echo TRACE2_DONE
