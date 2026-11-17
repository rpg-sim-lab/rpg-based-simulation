#!/bin/bash
# usage: runboth.sh <scratch dir> <base tree> <fix tree> <ticks> [smoke]   -- both arms, sequential, probe9, resumable, disk stop at 6 GB
S=$1; BASE=$2; FIX=$3; T=$4; TAG=${5:-full}
export PYTHONHASHSEED=0
mkdir -p $S/out9
for w in urban_political crowded_frontier frontier_living_world; do for s in 42 43 44 45 46; do
  [ "$TAG" = smoke ] && [ "$s" != 42 ] && continue
  for arm in base fix; do
    lab=${TAG}_${w}_s${s}_${arm}; [ -f $S/out9/$lab.done ] && continue
    A=$(df --output=avail -BM /mnt/data | tail -1 | tr -dc 0-9); [ "$A" -lt 6144 ] && { echo "STOP disk ${A}M before $lab"; exit 3; }
    tree=$BASE; [ $arm = fix ] && tree=$FIX
    cd $tree; export PYTHONPATH=$tree PROBE_OUT=$S/out9/$lab.jsonl
    systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 /mnt/data/venv-sync2/bin/python $S/probe9.py $w $s $T > $S/out9/$lab.stdout 2>&1 && touch $S/out9/$lab.done || { echo "FAIL $lab"; exit 5; }
    echo "DONE $lab $(date +%T)"
  done
  [ "$TAG" = smoke ] && break 2
done; done; echo ALL_DONE
