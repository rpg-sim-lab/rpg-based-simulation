#!/bin/bash
# Hash-equality check of the HOLD PR head 3a7ea995d against the stage-2 fix cells (rpg-planner's HOST FREE, two PLAIN runs, one at a time). Nothing is deleted; a non-empty tree dir or an existing output is REFUSED.
set -u
o=/mnt/data2/rpg-measure/holdmove; py=/mnt/data/venv-sync2/bin/python; wt=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/holdmove
HEAD_SHA=3a7ea995dd3498ce1cd1b3947ead02dbc1f872df; t=$o/tree_head_3a7ea995d; out=$o/head_hash; mkdir -p "$out"
[ "$(git -C $wt rev-parse HEAD)" = "$HEAD_SHA" ] || { echo "REFUSED: holdmove HEAD is not $HEAD_SHA"; exit 2; }
if [ -e "$t" ] && [ -n "$(ls -A "$t" 2>/dev/null)" ]; then echo "REFUSED: $t not empty"; exit 2; fi
mkdir -p "$t"; git -C $wt archive $HEAD_SHA | tar -x -C "$t" || { echo "STOP: archive failed"; exit 14; }
bad=0; n=0
while IFS=$'\t' read -r meta path; do set -- $meta; blob=$3; n=$((n+1)); [ -f "$t/$path" ] && [ "$(git -C $wt hash-object "$t/$path")" = "$blob" ] || { bad=$((bad+1)); echo "MISMATCH $path"; }; done < <(git -C $wt ls-tree -r $HEAD_SHA)
echo "tree_head verified against $HEAD_SHA: $n files, $bad mismatches"; [ $bad -eq 0 ] || exit 15
check() {
  local avail_kb free_kb; avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo); free_kb=$(df --output=avail -k /mnt/data | tail -1)
  echo "gate: MemAvailable=${avail_kb}kB /mnt/data free=${free_kb}kB $(date -u +%H:%M:%S)"
  [ "$avail_kb" -lt 3500000 ] && { echo "STOP: MemAvailable < 3500 MB"; exit 10; }
  [ "$free_kb" -lt 3000000 ] && { echo "STOP: /mnt/data free < 3 GB"; exit 11; }
  pgrep -f "[a]rm_child.py|[h]old_spy|[d]ying_window|[p]ytest|[v]3_trace_spy|[d]1_step0_spy" >/dev/null && { echo "STOP: another heavy job is running"; exit 12; }
  return 0
}
for cell in "frontier_marches 44" "urban_political 43"; do
  set -- $cell; world=$1; seed=$2; of=$out/head_plain_${world}_s${seed}.json
  [ -f "$of" ] && { echo "REFUSED: $of exists"; exit 2; }
  want=$($py -c "import json;print(json.load(open('$o/stage2/cells/fix_${world}_s${seed}_v7.json'))['final_hash'])")
  check; echo "start plain head $world s$seed expected=$want"
  V6_SUBJECT=-1 PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 /usr/bin/time -v -o "$of.time.txt" timeout 3600 bash -c "cd $t && $py $o/hold_spy_v7.py $world $seed 5000 $of PLAIN"
  rc=$?; got=$($py -c "import json;print(json.load(open('$of'))['final_hash'])" 2>/dev/null)
  echo "plain head $world s$seed rc=$rc got=$got expected=$want"
  [ "$got" = "$want" ] && echo "HASH EQUAL $world s$seed" || { echo "STOP: HASH MISMATCH $world s$seed"; exit 3; }
done
echo "BOTH EQUAL"; exit 0
