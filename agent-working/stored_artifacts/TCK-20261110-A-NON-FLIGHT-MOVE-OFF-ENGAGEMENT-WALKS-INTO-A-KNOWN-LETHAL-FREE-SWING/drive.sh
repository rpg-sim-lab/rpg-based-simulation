#!/bin/bash
# free_swing_trace.py runs, one at a time, UNCHANGED (sha256 checked before each).
S=/mnt/data2/scratch-b; O=$S/fst_out; PY=/mnt/data/scratch-deps-venv/bin/python
SCRIPT=$S/free_swing_trace_5c4b5da11.py; WANT=7c22df890e70e53b9eff3bc5547338c66e284a7b820c0c0265db8e6fbdefea20
R=/mnt/data2/rpg-measure
run() { # name sha9 world seed subjects cell
  got=$(sha256sum $SCRIPT | cut -c1-64); [ "$got" = "$WANT" ] || { echo "SHA_MISMATCH $1" >> $O/progress.txt; return; }
  t=$S/wt-$2; s=$(date +%s)
  (cd $t && PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout 3000 $PY $SCRIPT $3 $4 5000 $6 "$5" $O/$1.json) > $O/$1.log 2>&1
  echo "DONE $1 rc=$? wall=$(( $(date +%s)-s ))s $(tail -1 $O/$1.log)" >> $O/progress.txt
}
run flight_c42 83004a122 crowded_frontier 42 "14:323,3:2050,12:4971" $R/flight/results/fix_crowded_frontier_42.json
run flight_c43 83004a122 crowded_frontier 43 "37:1632,12:3053" $R/flight/results/fix_crowded_frontier_43.json
run def2_c43 3300928e8 crowded_frontier 43 "1:2942,8:2795" $R/results/3300928e88c4-72320cac-5000/crowded_frontier_43.json
run def2_c45 3300928e8 crowded_frontier 45 "5:1300" $R/results/3300928e88c4-72320cac-5000/crowded_frontier_45.json
run e24_u46 aa209f2d6 urban_political 46 "24:2418" $R/results/aa209f2d64f4-72320cac-5000/urban_political_46.json
echo ALL_DONE >> $O/progress.txt
