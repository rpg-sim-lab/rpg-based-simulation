#!/bin/bash
# NOT RUN by the author. K3 Phase 0 driver (rpg-designer-k3-plan-rulings.md 972600b672863882...; S9 record on #715 required first).
# Usage: OUT=<new dir on /mnt/data2> TREE=<fresh git-archive tree of the K3 base head e39fe7873> KIT=<the kit dir> bash $KIT/tools/rpg_measure/k3_phase0_launch.sh
# KIT LAYOUT: a tool checkout inside the kit dir ($KIT/tools/rpg_measure/{files} and $KIT/tools/test_architecture/pinned_runner.py), SHA256SUMS at $KIT (relative paths).
# One cell, ONE process at a time, each behind its own host gate: urban_political s42 2400t: the PLAIN twin (its final hash is the BASELINE CHECK: it must equal 2a6e74f0 or the 30-loss baseline does not carry over), then the SPY with the twin's hash.
# Exit codes: 1 kit sha mismatch / pinned_runner missing, 9 host busy / OUT exists, 15 disk floor, 18 a used tree named, 13 plain rc, 124 timeout, 2 the summary has a flag (BASELINE hash differs, or a HARD D3 cycle), otherwise the spy own (3 hash, 6 finding, 8 exception).
# The caller runs `. /mnt/data2/rpg-measure/lib/busy_gate.sh; rpg_host_gate` as its OWN command first. Writes only under $OUT; nothing is deleted. LAUNCH_DRY_RUN=1 prints the cell and exits.
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
py=${PY:-/mnt/data/venv-sync2/bin/python}
: "${OUT:?}" "${TREE:?}" "${KIT:?}"
[ -f "$KIT/tools/test_architecture/pinned_runner.py" ] || { echo "STOP: $KIT/tools/test_architecture/pinned_runner.py is missing (the kit must be laid out as a tool checkout)"; exit 1; }
case "$TREE" in *w781_*|*w995*|*tree_995*|*base_tree_995*|*tgt_6ee88*|*trace_v6_tree*|*fixtree_trace*|*h3fix_13844_tree*|*v8fix_*|*k2k3_tree*|*k2fix_tree*) echo "STOP: a used tree was named; use a fresh extract"; exit 18;; esac
W=urban_political; S=42; T=2400
BASELINE=2a6e74f04cd735a15215a19d34f099a01d006cff6ee571627dd06372a801fbbd
run() { # outjson mode [plainhash]
  local tmo; tmo=$($py -c "import math;print(math.ceil($T*0.5)+600)")
  local extra=""; [ -n "${3:-}" ] && extra="--plain-hash $3"
  SIM_OBS_MODE=OFF RPG_OBS_MODE=OFF PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$TREE systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout "$tmo" \
    bash -c "cd $TREE && $py $KIT/tools/rpg_measure/k3_phase0_spy.py $W $S $T $1 --mode $2 $extra" > "${1%.json}.log" 2>&1
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then echo "CELL $W s$S ${T}t: plain (the baseline check, expects $BASELINE) then spy (cwd=$TREE PYTHONPATH=$TREE) $py $KIT/tools/rpg_measure/k3_phase0_spy.py $W $S $T $OUT/${W}_s${S}_t${T}_{plain,spy}.json --mode {plain,spy} [--plain-hash <twin hash>]"; exit 0; fi
[ -e "$OUT" ] && { echo "STOP: out dir exists: $OUT"; exit 9; }
(cd "$KIT" && sha256sum -c SHA256SUMS) || { echo "STOP: kit sha mismatch"; exit 1; }
mkdir -p "$OUT"
gate() { rpg_host_gate || exit 9; f=$(df --output=avail -k /mnt/data2 | tail -1); [ "$f" -lt 3000000 ] && { echo "STOP: /mnt/data2 < 3 GB"; exit 15; }
         a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3670016 ] || { echo "STOP: MemAvailable < 3.5 GB"; exit 9; }; return 0; }
b="$OUT/${W}_s${S}_t${T}"
gate; run "${b}_plain.json" plain; rc=$?; [ $rc -eq 124 ] && { echo "STOP: TIMEOUT plain"; exit 124; }; [ $rc -ne 0 ] && { echo "STOP: plain rc=$rc"; exit 13; }
full=$($py -I -B -c "import json;print(json.load(open('${b}_plain.json'))['final_hash'])")
echo "baseline check: plain final_hash $full (expected $BASELINE): $([ "$full" = "$BASELINE" ] && echo EQUAL || echo DIFFERENT)"
gate; run "${b}_spy.json" spy "$full"; rc=$?; echo "spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc (3 hash != plain VOID, 6 finding, 8 exception, 124 timeout)"; exit $rc; }
$py -I -B "$KIT/tools/rpg_measure/k3_phase0_summary.py" "$OUT"; rc=$?; echo "driver_rc=$rc"; [ $rc -eq 0 ] || exit $rc
