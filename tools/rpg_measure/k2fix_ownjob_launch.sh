#!/bin/bash
# NOT RUN by the author. K2 fix own-job measurement driver (rpg-designer-k2-fix-plan-rulings.md a73bc655d487395b; S9 record on #715 required first).
# Usage: OUT=<new dir on /mnt/data2> TREE_MAIN=<fresh git-archive tree of main d084b9248> TREE_FIX=<fresh git-archive tree of the fix head> KIT=<the kit dir> bash $KIT/tools/rpg_measure/k2fix_ownjob_launch.sh
# KIT LAYOUT: a tool checkout inside the kit dir ($KIT/tools/rpg_measure/{files} and $KIT/tools/test_architecture/pinned_runner.py), SHA256SUMS at $KIT (relative paths).
# Cells (ONE process at a time, each behind its own host gate): per cell and per arm (main, then fix) the PLAIN twin, then the SPY with the twin's hash (a spy hash != plain hash is VOID, rc 3):
#   crowded_frontier s42 5000t, frontier_living_world s42 5000t, urban_political s42 5000t, urban_political s42 2400t (the cell that holds the v6 rows).
# Exit codes: 1 kit sha mismatch / pinned_runner missing, 9 host busy / OUT exists, 15 disk floor, 18 a used tree named, 13 plain rc, 124 timeout, otherwise the spy's own (3 hash, 6 finding, 8 exception).
# The caller runs `. /mnt/data2/rpg-measure/lib/busy_gate.sh; rpg_host_gate` as its OWN command first. Writes only under $OUT; nothing is deleted. LAUNCH_DRY_RUN=1 prints the cells and exits.
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
py=${PY:-/mnt/data/venv-sync2/bin/python}
: "${OUT:?}" "${TREE_MAIN:?}" "${TREE_FIX:?}" "${KIT:?}"
[ -f "$KIT/tools/test_architecture/pinned_runner.py" ] || { echo "STOP: $KIT/tools/test_architecture/pinned_runner.py is missing (the kit must be laid out as a tool checkout)"; exit 1; }
for t in "$TREE_MAIN" "$TREE_FIX"; do case "$t" in *w781_*|*w995*|*tree_995*|*base_tree_995*|*tgt_6ee88*|*trace_v6_tree*|*fixtree_trace*|*h3fix_13844_tree*|*v8fix_*|*k2k3_tree_main*|*k2k3_tree2_main*) echo "STOP: a used tree was named; use a fresh extract"; exit 18;; esac; done
CELLS="crowded_frontier:42:5000 frontier_living_world:42:5000 urban_political:42:5000 urban_political:42:2400"
run() { # tree world seed ticks outjson mode [plainhash]
  local tmo; tmo=$($py -c "import math;print(math.ceil($4*0.5)+600)")
  local extra=""; [ -n "${7:-}" ] && extra="--plain-hash $7"
  SIM_OBS_MODE=OFF RPG_OBS_MODE=OFF PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$1 systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout "$tmo" \
    bash -c "cd $1 && $py $KIT/tools/rpg_measure/k2fix_ownjob_spy.py $2 $3 $4 $5 --mode $6 $extra" > "${5%.json}.log" 2>&1
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  for c in $CELLS; do IFS=: read -r w s t <<< "$c"; for arm in main fix; do tree=$TREE_MAIN; [ "$arm" = fix ] && tree=$TREE_FIX; echo "CELL $arm $w s$s ${t}t: plain then spy (cwd=$tree) $py $KIT/tools/rpg_measure/k2fix_ownjob_spy.py $w $s $t $OUT/$arm/${w}_s${s}_t${t}_{plain,spy}.json --mode {plain,spy} [--plain-hash <twin hash>]"; done; done
  exit 0
fi
[ -e "$OUT" ] && { echo "STOP: out dir exists: $OUT"; exit 9; }
(cd "$KIT" && sha256sum -c SHA256SUMS) || { echo "STOP: kit sha mismatch"; exit 1; }
mkdir -p "$OUT/main" "$OUT/fix"
gate() { rpg_host_gate || exit 9; f=$(df --output=avail -k /mnt/data2 | tail -1); [ "$f" -lt 3000000 ] && { echo "STOP: /mnt/data2 < 3 GB"; exit 15; }
         a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3670016 ] || { echo "STOP: MemAvailable < 3.5 GB"; exit 9; }; return 0; }
for c in $CELLS; do
  IFS=: read -r w s t <<< "$c"
  for arm in main fix; do
    tree=$TREE_MAIN; [ "$arm" = fix ] && tree=$TREE_FIX; b="$OUT/$arm/${w}_s${s}_t${t}"
    gate; run "$tree" "$w" "$s" "$t" "${b}_plain.json" plain; rc=$?; [ $rc -eq 124 ] && { echo "STOP: TIMEOUT plain $arm $w s$s"; exit 124; }; [ $rc -ne 0 ] && { echo "STOP: plain rc=$rc ($arm $w s$s t$t)"; exit 13; }
    full=$($py -I -B -c "import json;print(json.load(open('${b}_plain.json'))['final_hash'])")
    gate; run "$tree" "$w" "$s" "$t" "${b}_spy.json" spy "$full"; rc=$?; echo "$arm $w s$s t$t spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc ($arm $w s$s t$t): 3 hash != plain (VOID), 6 finding, 8 exception, 124 timeout"; exit $rc; }
  done
done
$py -I -B "$KIT/tools/rpg_measure/k2fix_ownjob_summary.py" "$OUT"; rc=$?; echo "driver_rc=$rc"; exit $rc
