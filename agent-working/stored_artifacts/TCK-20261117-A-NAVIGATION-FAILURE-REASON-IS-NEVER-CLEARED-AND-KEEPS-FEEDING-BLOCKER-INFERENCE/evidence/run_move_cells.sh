#!/bin/bash
# DRAFT driver (stale-failure-reason RERUN, new S9). Needs the designer's sha approval of the kit, an S9 record and rpg-planner's HOST FREE. 6 processes: per cell a PLAIN twin, then the move spy with the twin's full hash (the spy exits 3 on a mismatch).
# Tree = TREE (REQUIRED, no default: the git archive of the fix commit that passed the statics and the targeted tests). Before EACH process: the shared host gate (lib/busy_gate.sh v3, 3500 MB floor) plus a local check for a running move spy.
# The spy sha256 is checked at start (exit 14). stderr goes to the cell log. Nothing is deleted.
set -u
. /mnt/data2/rpg-measure/lib/busy_gate.sh
o=/mnt/data2/rpg-measure/failreason/diag2; py=/mnt/data/venv-sync2/bin/python
[ -n "${TREE:-}" ] && [ -d "$TREE/src" ] || { echo "STOP: TREE is not set to a tree with src/"; exit 15; }
t=$TREE
spy=$o/failreason_move_spy.py; want_sha=9c0b7c56471ead2f7d36f06760ed12a235facf8eb6364fcffa57b2e99ba9a1ec
ticks=${TICKS:-5000}; cells=${CELLS:-"frontier_living_world:42 urban_political:42 crowded_frontier:42"}; out=${OUT:-$o/cells_move}
[ "$(sha256sum "$spy" | cut -d' ' -f1)" = "$want_sha" ] || { echo "STOP: spy sha mismatch"; exit 14; }
mkdir -p "$out"
gate() {
  rpg_host_gate || exit 9
  pgrep -af "[p]ython.*failreason_move_spy" | grep -qE "rpg-measure" && { echo "STOP: a move spy is running"; exit 12; }
  local f; f=$(df --output=avail -k /mnt/data2 | tail -1)
  [ "$f" -lt 3000000 ] && { echo "STOP: /mnt/data2 < 3 GB"; exit 11; }
  return 0
}
run() { # $1 world $2 seed $3 out json $4 PLAIN|hash
  PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0 timeout 3600 bash -c "cd $t && $py $spy $1 $2 $ticks $3 $4" > "${3%.json}.log" 2>&1
}
for cell in $cells; do
  w=${cell%%:*}; s=${cell##*:}
  gate; run "$w" "$s" "$out/${w}_s${s}_plain.json" PLAIN || { echo "STOP: plain twin failed rc=$? (see ${w}_s${s}_plain.log)"; exit 13; }
  full=$($py -c "import json;print(json.load(open('$out/${w}_s${s}_plain.json'))['final_hash'])")
  gate; run "$w" "$s" "$out/${w}_s${s}_spy.json" "$full"; rc=$?
  echo "$w s$s spy rc=$rc"; [ $rc -ne 0 ] && { echo "STOP: spy rc=$rc (see ${w}_s${s}_spy.log)"; exit $rc; }
done
exit 0
