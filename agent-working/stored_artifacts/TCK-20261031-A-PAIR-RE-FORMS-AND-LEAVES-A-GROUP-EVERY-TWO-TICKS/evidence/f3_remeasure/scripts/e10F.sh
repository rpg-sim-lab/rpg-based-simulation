#!/bin/bash
# short run: crowded s43 arm effd2e8fc to t905, watch 10,27,30,4,29 at t880-898 (tactical calls and tuples for those entities and every entity within Euclid 10 of them); control: death list equals C's up to the stop
T=/data/vboxuser/Work/groups_base; PY=/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python; O=$T/out_t2; sha=effd2e8fc
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus PYTHONHASHSEED=0
m=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$m" -ge 3145728 ] || { echo "E10_STOP memory $m"; exit 3; }
sw=$(awk '/SwapTotal/{t=$2}/SwapFree/{f=$2}END{print t-f}' /proc/meminfo); cd $T/trees/$sha; ST=$(date +%s)
WINS="880-898:10;880-898:27;880-898:30;880-898:4;880-898:29" CTRLWIN=0,-1 TR_OUT=$O/crowded_s43_e10.jsonl PYTHONPATH=$T/trees/$sha systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 $PY $T/trace_t2.py crowded_frontier 43 905 0 > $O/crowded_s43_e10.stdout 2>&1
echo "E10 rc=$? wall_s=$(( $(date +%s)-ST )) $(tail -1 $O/crowded_s43_e10.stdout) mem_start_kB=$m swap_used_kB=$sw"; echo E10_DONE
