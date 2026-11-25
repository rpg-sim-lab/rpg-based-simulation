#!/bin/bash
# NOT RUN by the author. K2/K3 re-count driver (rpg-designer's fixed definitions, sha256 992b7ce37e1a...940cd5855; dispatch #715 plan 7157615913, K list 7157730160).
# Usage: OUT=<new dir on /mnt/data2> TREE=<fresh git-archive tree of main d084b9248> KIT=<dir holding the kit files + SHA256SUMS> k2k3_count_launch.sh
# STAGE=neg (FIRST, before stage 1, under the S9): the real-kernel NEGATIVE control, urban_political s42, 2,400 t, plain + spy (--neg), then `summary --neg` lists every K2 run > 10 with lodged_in, sleep_debt and payload; a REST run whose subject was lodged at its building = STOP (rc 2), to the designer. STAGE=1 (default): the four stage-1 cells. STAGE=2: frontier_living_world s43-46 (Amendment 1, A3), run ONLY when the stage-1 s42 total is 0 (the summary prints the K3 rule). Cells (ONE process at a time, each behind its own host gate): per cell the PLAIN twin, then the SPY with the twin's hash (a spy hash != plain hash is VOID, rc 3):
#   crowded_frontier s42, frontier_living_world s42, urban_political s42, urban_political s46 (K2's extra seed), each 5000 t.
# Exit codes: 1 kit sha mismatch, 9 host busy / OUT exists, 15 disk floor, 18 a used tree named, 13 plain rc, 124 timeout, otherwise the spy's own (3 hash, 4 reach void, 5 probe error, 6 field finding, 8 spy exception).
# The caller runs `. /mnt/data2/rpg-measure/lib/busy_gate.sh; rpg_host_gate` as its OWN command first (rc 9 = STOP). Writes only under $OUT; nothing is deleted.
# STAGE=2 also takes STAGE1_OUT=<the stage-1 OUT dir> so the final summary sees all 7 cells.
# LAUNCH_DRY_RUN=1 prints the cell list and the exact process command lines, then exits (no process, no gate).
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
py=${PY:-/mnt/data/venv-sync2/bin/python}
: "${OUT:?}" "${TREE:?}" "${KIT:?}"
TICKS=${TICKS:-5000}
case "$TREE" in *w781_*|*w995*|*tree_995*|*base_tree_995*|*tgt_6ee88*|*trace_v6_tree*|*fixtree_trace*|*h3fix_13844_tree*|*v8fix_*) echo "STOP: a used tree was named; use a fresh extract"; exit 18;; esac
STAGE=${STAGE:-1}
case "$STAGE" in 1) CELLS="crowded_frontier:42 frontier_living_world:42 urban_political:42 urban_political:46";; 2) CELLS="frontier_living_world:43 frontier_living_world:44 frontier_living_world:45 frontier_living_world:46";; neg) CELLS="urban_political:42"; TICKS=2400;; *) echo "STOP: STAGE must be neg, 1 or 2"; exit 9;; esac
NEGFLAG=""; [ "$STAGE" = neg ] && NEGFLAG="--neg"
run() { # world seed outjson mode [plainhash]
  local tmo; tmo=$($py -c "import math;print(math.ceil($TICKS*0.5)+600)")
  local extra=""; [ -n "${5:-}" ] && extra="--plain-hash $5"
  SIM_OBS_MODE=OFF RPG_OBS_MODE=OFF PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$TREE systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout "$tmo" \
    bash -c "cd $TREE && $py $KIT/k2k3_count_spy.py $1 $2 $TICKS $3 --mode $4 $extra $NEGFLAG" > "${3%.json}.log" 2>&1
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  for c in $CELLS; do w=${c%%:*}; s=${c##*:}; echo "CELL $w s$s ${TICKS}t: plain then spy (cwd=$TREE PYTHONPATH=$TREE) $py $KIT/k2k3_count_spy.py $w $s $TICKS $OUT/${w}_s${s}_{plain,spy}.json --mode {plain,spy} [--plain-hash <twin hash>]"; done
  exit 0
fi
[ -e "$OUT" ] && { echo "STOP: out dir exists: $OUT"; exit 9; }
(cd "$KIT" && sha256sum -c SHA256SUMS) || { echo "STOP: kit sha mismatch"; exit 1; }
mkdir -p "$OUT"
gate() { rpg_host_gate || exit 9; f=$(df --output=avail -k /mnt/data2 | tail -1); [ "$f" -lt 3000000 ] && { echo "STOP: /mnt/data2 < 3 GB"; exit 15; }
         a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3670016 ] || { echo "STOP: MemAvailable < 3.5 GB"; exit 9; }; return 0; }
for c in $CELLS; do
  w=${c%%:*}; s=${c##*:}; b="$OUT/${w}_s${s}"
  gate; run "$w" "$s" "${b}_plain.json" plain; rc=$?; [ $rc -eq 124 ] && { echo "STOP: TIMEOUT plain $w s$s"; exit 124; }; [ $rc -ne 0 ] && { echo "STOP: plain rc=$rc ($w s$s)"; exit 13; }
  full=$($py -I -B -c "import json;print(json.load(open('${b}_plain.json'))['final_hash'])")
  gate; run "$w" "$s" "${b}_spy.json" spy "$full"; rc=$?; echo "$w s$s spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc ($w s$s): 3 hash != plain (VOID), 4 reach void, 5 probe error, 6 field finding, 8 spy exception, 124 timeout"; exit $rc; }
done
if [ "$STAGE" = neg ]; then $py -I -B "$KIT/k2k3_count_summary.py" --neg "$OUT"; rc=$?; echo "driver_rc=$rc"; exit $rc; fi
$py -I -B "$KIT/k2k3_count_summary.py" ${STAGE1_OUT:+"$STAGE1_OUT"} "$OUT"; echo "driver_rc=$?"
