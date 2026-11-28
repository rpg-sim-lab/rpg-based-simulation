#!/bin/bash
# NOT RUN by the author. Perception-gate calibration own-job driver (TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT; rpg-designer ruling 9c42fb88; S9 record on #715 required first).
# Usage: ARM=base|fix OUT=<new dir on /mnt/data2> TREE=<fresh git-archive tree of the arm's head> KIT=<the kit dir> [STAGE=1|smoke] bash $KIT/tools/rpg_measure/perception_gate_calibration_launch.sh   [BASE_OUT=<the base arm's OUT dir, ARM=fix only>]
# Arms: BASE = main ac759e0ba, FIX = the calibration head. EACH arm runs the PLAIN cell first (timed, final hash), then the SPY with the plain hash (spy hash != plain = VOID rc 3): H1 on both arms.
# STAGE=1 (default): crowded_frontier, frontier_living_world, urban_political, each s42, 1000 t, recording OFF. STAGE=smoke: ONE short cell (frontier_living_world s42, SMOKE_TICKS, default 300) end to end.
# Exit codes: 1 kit sha mismatch / pinned_runner missing, 9 host busy / OUT exists / bad stage, 15 disk floor, 18 a used tree named, 13 plain rc, 124 timeout, 3 / 6 / 8 a spy cell void (hash / finding / exception),
# 2 / 4 / 5 the summary (a HARD failure / a collapse to 0 STOP / no cells). The caller runs `. /mnt/data2/rpg-measure/lib/busy_gate.sh; rpg_host_gate` as its OWN command first.
# Writes only under $OUT (the kernel's run dirs go to $OUT/runs, never into the frozen tree); nothing is deleted. LAUNCH_DRY_RUN=1 prints the cells and exits.
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
py=${PY:-/mnt/data/venv-sync2/bin/python}
: "${ARM:?}" "${OUT:?}" "${TREE:?}" "${KIT:?}"
[ "$ARM" = base ] || [ "$ARM" = fix ] || { echo "STOP: ARM must be base or fix"; exit 9; }
[ -f "$KIT/tools/test_architecture/pinned_runner.py" ] || { echo "STOP: $KIT/tools/test_architecture/pinned_runner.py is missing (the kit must be laid out as a tool checkout)"; exit 1; }
case "$TREE" in *w781_*|*w995*|*tree_995*|*base_tree_995*|*tgt_6ee88*|*trace_v6_tree*|*fixtree_trace*|*h3fix_13844_tree*|*v8fix_*|*k2k3_tree*|*k2fix_tree*|*k3_phase0_tree*|*tree_base_4af5ef2a3*|*tree_fix_f5a520daf*) echo "STOP: a used tree was named; use a fresh extract"; exit 18;; esac
STAGE=${STAGE:-1}
case "$STAGE" in
  1) CELLS="crowded_frontier:42:1000 frontier_living_world:42:1000 urban_political:42:1000";;
  smoke) CELLS="frontier_living_world:42:${SMOKE_TICKS:-300}";;
  *) echo "STOP: STAGE must be 1 or smoke"; exit 9;;
esac
run() { # world seed ticks outjson mode [plainhash]
  local tmo; tmo=$($py -c "import math;print(math.ceil($3*0.7)+600)")
  local extra=""; [ -n "${6:-}" ] && extra="--plain-hash $6"
  SIM_OBS_MODE=OFF RPG_OBS_MODE=OFF PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$TREE systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout "$tmo" \
    bash -c "cd $TREE && $py $KIT/tools/rpg_measure/perception_gate_calibration_spy.py $1 $2 $3 $4 --mode $5 --arm $ARM --run-root $OUT/runs $extra" > "${4%.json}.log" 2>&1
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  for c in $CELLS; do IFS=: read w s t <<< "$c"; echo "CELL $ARM $w s$s ${t}t: plain then spy (cwd=$TREE PYTHONPATH=$TREE) $py $KIT/tools/rpg_measure/perception_gate_calibration_spy.py $w $s $t $OUT/${w}_s${s}_t${t}_{plain,spy}.json"; done
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
  full=$($py -I -B -c "import json;print(json.load(open('${b}_plain.json'))['final_hash'])"); echo "$ARM $w s$s ${t}t plain $full"
  gate; run "$w" "$s" "$t" "${b}_spy.json" spy "$full"; rc=$?; echo "$ARM $w s$s ${t}t spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc: 3 hash != plain (VOID), 6 finding, 8 spy exception, 124 timeout"; exit $rc; }
done
if [ "$ARM" = fix ]; then SMOKEFLAG=""; [ "$STAGE" = smoke ] && SMOKEFLAG="--smoke"; $py -I -B "$KIT/tools/rpg_measure/perception_gate_calibration_summary.py" $SMOKEFLAG "${BASE_OUT:?BASE_OUT is needed for ARM=fix}" "$OUT"; rc=$?; echo "summary rc=$rc (0 ok, 2 HARD failure, 4 collapse to 0 STOP, 5 no cells)"; exit $rc; fi
exit 0
