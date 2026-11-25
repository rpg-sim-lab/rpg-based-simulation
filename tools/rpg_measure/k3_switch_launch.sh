#!/bin/bash
# NOT RUN by the author. K3 own-job driver (rpg-designer-k3-plan-rulings.md 972600b6...; S9 record on #715 required first).
# Usage: ARM=base|fix OUT=<new dir on /mnt/data2> TREE=<fresh git-archive tree of the arm's head> KIT=<the kit dir> bash $KIT/tools/rpg_measure/k3_switch_launch.sh   [BASE_OUT=<the base arm's OUT dir>  (ARM=fix only: the summary)]
# KIT LAYOUT: a tool checkout inside the kit dir ($KIT/tools/rpg_measure/{files} and $KIT/tools/test_architecture/pinned_runner.py), SHA256SUMS at $KIT (relative paths).
# Cells (ONE process at a time, each behind its own host gate): crowded_frontier s42 5000t, frontier_living_world s42 5000t, urban_political s42 5000t, urban_political s42 2400t.
# ARM=base: the PLAIN twin only, on the base head (e39fe7873) tree: the neutrality references. ARM=fix: per cell the PLAIN twin, then the SPY with the twin's hash (spy hash != plain = VOID rc 3); the summary compares with BASE_OUT.
# Exit codes: 1 kit sha mismatch / pinned_runner missing, 9 host busy / OUT exists, 15 disk floor, 18 a used tree named, 13 plain rc, 124 timeout, 2 the summary has a failed bar, otherwise the spy's own (3 hash, 6 finding, 8 exception).
# The caller runs `. /mnt/data2/rpg-measure/lib/busy_gate.sh; rpg_host_gate` as its OWN command first. Writes only under $OUT; nothing is deleted. LAUNCH_DRY_RUN=1 prints the cells and exits.
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
py=${PY:-/mnt/data/venv-sync2/bin/python}
: "${ARM:?}" "${OUT:?}" "${TREE:?}" "${KIT:?}"
[ "$ARM" = base ] || [ "$ARM" = fix ] || { echo "STOP: ARM must be base or fix"; exit 9; }
[ -f "$KIT/tools/test_architecture/pinned_runner.py" ] || { echo "STOP: $KIT/tools/test_architecture/pinned_runner.py is missing (the kit must be laid out as a tool checkout)"; exit 1; }
case "$TREE" in *w781_*|*w995*|*tree_995*|*base_tree_995*|*tgt_6ee88*|*trace_v6_tree*|*fixtree_trace*|*h3fix_13844_tree*|*v8fix_*|*k2k3_tree*|*k2fix_tree*|*k3_phase0_tree*) echo "STOP: a used tree was named; use a fresh extract"; exit 18;; esac
CELLS="crowded_frontier:42:5000 frontier_living_world:42:5000 urban_political:42:5000 urban_political:42:2400"
run() { # world seed ticks outjson mode [plainhash]
  local tmo; tmo=$($py -c "import math;print(math.ceil($3*0.5)+600)")
  local extra=""; [ -n "${6:-}" ] && extra="--plain-hash $6"
  SIM_OBS_MODE=OFF RPG_OBS_MODE=OFF PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$TREE systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout "$tmo" \
    bash -c "cd $TREE && $py $KIT/tools/rpg_measure/k3_switch_spy.py $1 $2 $3 $4 --mode $5 $extra" > "${4%.json}.log" 2>&1
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  for c in $CELLS; do IFS=: read w s t <<< "$c"; echo "CELL $ARM $w s$s ${t}t: plain$([ "$ARM" = fix ] && echo ' then spy') (cwd=$TREE PYTHONPATH=$TREE) $py $KIT/tools/rpg_measure/k3_switch_spy.py $w $s $t $OUT/${w}_s${s}_t${t}_{plain,spy}.json --mode {plain,spy}"; done
  exit 0
fi
[ -e "$OUT" ] && { echo "STOP: out dir exists: $OUT"; exit 9; }
(cd "$KIT" && sha256sum -c SHA256SUMS) || { echo "STOP: kit sha mismatch"; exit 1; }
mkdir -p "$OUT"
gate() { rpg_host_gate || exit 9; f=$(df --output=avail -k /mnt/data2 | tail -1); [ "$f" -lt 3000000 ] && { echo "STOP: /mnt/data2 < 3 GB"; exit 15; }
         a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3670016 ] || { echo "STOP: MemAvailable < 3.5 GB"; exit 9; }; return 0; }
for c in $CELLS; do
  IFS=: read w s t <<< "$c"; b="$OUT/${w}_s${s}_t${t}"
  gate; run "$w" "$s" "$t" "${b}_plain.json" plain; rc=$?; [ $rc -eq 124 ] && { echo "STOP: TIMEOUT plain $w s$s"; exit 124; }; [ $rc -ne 0 ] && { echo "STOP: plain rc=$rc ($w s$s ${t}t)"; exit 13; }
  full=$($py -I -B -c "import json;print(json.load(open('${b}_plain.json'))['final_hash'])"); echo "$w s$s ${t}t plain $full"
  [ "$ARM" = base ] && continue
  gate; run "$w" "$s" "$t" "${b}_spy.json" spy "$full"; rc=$?; echo "$w s$s ${t}t spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc: 3 hash != plain (VOID), 6 finding, 8 spy exception, 124 timeout"; exit $rc; }
done
if [ "$ARM" = fix ]; then $py -I -B "$KIT/tools/rpg_measure/k3_switch_summary.py" "$OUT" "${BASE_OUT:?BASE_OUT is needed for ARM=fix}"; rc=$?; echo "driver_rc=$rc"; exit $rc; fi
