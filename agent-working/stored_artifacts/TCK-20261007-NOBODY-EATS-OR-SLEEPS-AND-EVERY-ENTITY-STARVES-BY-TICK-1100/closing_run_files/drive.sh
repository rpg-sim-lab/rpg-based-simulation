#!/bin/bash
D=/mnt/data2/rpg-measure/nobody-eats
for w in frontier_living_world crowded_frontier; do
  for r in a b; do
    $D/run_cell.sh ${w}_$r $D/world_cell.py $w 42 2000 $D/${w}_$r.json || { echo "STOP at ${w}_$r" >> $D/status.txt; exit 1; }
  done
  ha=$(python3 -c "import json;print(json.load(open('$D/${w}_a.json'))['final_hash'])"); hb=$(python3 -c "import json;print(json.load(open('$D/${w}_b.json'))['final_hash'])")
  if [ "$ha" != "$hb" ]; then echo "STOP hash mismatch $w $ha $hb" >> $D/status.txt; exit 1; fi
  echo "$w twin hashes equal $ha" >> $D/status.txt
done
$D/run_cell.sh b5k $D/b5k_cell.py $D/b5k.json || { echo "STOP at b5k" >> $D/status.txt; exit 1; }
echo ALL_DONE >> $D/status.txt
