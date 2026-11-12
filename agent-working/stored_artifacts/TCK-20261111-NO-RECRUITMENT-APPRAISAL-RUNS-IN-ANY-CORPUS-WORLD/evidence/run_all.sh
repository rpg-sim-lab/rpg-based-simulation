#!/bin/bash
# sequential: 4 PLAIN s42 twins, then 20 spied cells. exit 3 on s42 = STOP.
t=/mnt/data2/rpg-measure/recruit/tree; o=/mnt/data2/rpg-measure/recruit/out; spy=/mnt/data2/rpg-measure/recruit/recruit_spy.py
W="crowded_frontier urban_political frontier_living_world highland_traverse"
run(){ ( cd $t && PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout 1800 /mnt/data/venv-sync2/bin/python $spy "$@" ) ; }
for w in $W; do
  pgrep -af "arm_child|pytest" | grep -v pgrep && { echo "HOST BUSY before twin $w"; exit 9; }
  run $w 42 5000 $o/${w}_42_PLAIN.json PLAIN > $o/${w}_42_PLAIN.log 2>&1; echo "twin $w rc=$?"
done
for w in $W; do for s in 42 43 44 45 46; do
  pgrep -af "arm_child|pytest" | grep -v pgrep && { echo "HOST BUSY before $w $s"; exit 9; }
  if [ $s = 42 ]; then h=$(python3 -c "import json;print(json.load(open('$o/${w}_42_PLAIN.json'))['final_hash'])"); else h=""; fi
  run $w $s 5000 $o/${w}_$s.json $h > $o/${w}_$s.log 2>&1; rc=$?; echo "cell $w $s rc=$rc"
  [ $rc = 3 ] && [ $s = 42 ] && { echo "STOP hash mismatch $w"; exit 3; }
done; done
echo ALL_DONE
