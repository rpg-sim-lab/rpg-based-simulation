#!/bin/bash
S=$1; cd /mnt/data/Working/rpg-based-simulation/.claude/worktrees/retreat
export PYTHONHASHSEED=0 PYTHONPATH=.
for w in urban_political crowded_frontier frontier_living_world; do for s in 42 43 44 45 46; do
  lab=${w}_s${s}_main; [ -f $S/out/$lab.done ] && continue
  [ "$w:$s" = "urban_political:42" ] && { touch $S/out/$lab.done; continue; }
  A=$(df --output=avail -BM /mnt/data | tail -1 | tr -dc 0-9); [ "$A" -lt 6144 ] && { echo "STOP disk ${A}M before $lab"; exit 3; }
  export PROBE_OUT=$S/out/$lab.jsonl
  systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 /mnt/data/venv-sync2/bin/python $S/probe7.py $w $s 2000 > $S/out/$lab.stdout 2>&1 && touch $S/out/$lab.done || { echo "FAIL $lab"; exit 5; }
  echo "DONE $lab $(date +%T)"
done; done; echo ALL_DONE
