#!/bin/bash
# STAGE 2 driver (needs rpg-planner's HOST FREE + the designer's approval of every sha it uses). 3 worlds x seeds 42-46 x 5000 ticks x {base, fix} = 30 spied runs with hold_spy_v7.py,
# plus 3 fix-arm plain twins (fm s43, crowded s45, urban s44) and 1 base-arm plain control (crowded s43) = 34 runs. One at a time. No deletes: refuses a non-empty $out and non-empty tree dirs.
# BASE = origin/main f94417e6f; FIX = holdmove HEAD b9d78c427 (origin/main merged into it); the merge-base of the two must equal BASE exactly (checked and logged).
# A cell with a plain twin runs the plain first and pins its spied cell to that hash (spy exit 3 = hash mismatch = STOP, the whole set is void). After each FIX cell stage2_check.py cell is run; after
# seed 46 of a world stage2_check.py world is run. exit 20 / 21 = a stop tripped (report; no retry). Before each run: MemAvailable >= 3500 MB, /mnt/data >= 3 GB, no heavy job (bracketed patterns).
set -u
o=/mnt/data2/rpg-measure/holdmove
s2=$o/stage2
out=$s2/cells
py=/mnt/data/venv-sync2/bin/python
wt=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/holdmove
BASE=f94417e6f58f72e0e4289b217df1b0dd9f5bc4e7
FIX=b9d78c427280c636d71c67490dda2c8b6c708717
# RESUME=1 (explicit): continue a stopped set. Existing cells are never deleted or overwritten: a cell whose _v7.json exists is skipped (and, for a pinned cell, its _plain.json is reused, never re-run); the existing trees
# are re-verified against their shas (blob hashes of every tracked file) instead of re-extracted; stage2_check cell is re-run on every existing fix cell first (any non-zero = STOP). Without RESUME the refusals below stay.
RESUME=${RESUME:-}
mkdir -p "$s2" "$out"
if [ -z "$RESUME" ]; then
  if [ -n "$(ls -A "$out")" ]; then echo "REFUSED: $out not empty (deleting a previous result is the user's call)"; exit 2; fi
  for d in tree_base tree_fix; do if [ -e "$s2/$d" ] && [ -n "$(ls -A "$s2/$d")" ]; then echo "REFUSED: $s2/$d not empty"; exit 2; fi; done
else
  echo "RESUME=1: existing cells are kept and skipped; nothing is deleted or overwritten"
fi
[ "$(git -C $wt rev-parse HEAD)" = "$FIX" ] || { echo "REFUSED: holdmove HEAD is not $FIX"; exit 2; }
mb=$(git -C $wt merge-base $FIX $BASE); echo "FIX=$FIX BASE=$BASE merge-base=$mb"
[ "$mb" = "$BASE" ] || { echo "REFUSED: merge-base != BASE"; exit 2; }
check() {
  local avail_kb free_kb
  avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo); free_kb=$(df --output=avail -k /mnt/data | tail -1)
  echo "gate: MemAvailable=${avail_kb}kB /mnt/data free=${free_kb}kB $(date -u +%H:%M:%S)"
  if [ "$avail_kb" -lt 3500000 ]; then echo "STOP: MemAvailable ${avail_kb} kB < 3500 MB"; exit 10; fi
  if [ "$free_kb" -lt 3000000 ]; then echo "STOP: /mnt/data free ${free_kb} kB < 3 GB -- tell rpg-planner"; exit 11; fi
  if pgrep -f "[a]rm_child.py|[h]old_spy|[p]ytest|[v]3_trace_spy|[d]1_step0_spy" >/dev/null; then echo "STOP: another heavy job is running"; exit 12; fi
}
verify_tree() { # $1=arm $2=sha: every tracked blob (git ls-tree -r, no path filter) at the sha must exist unchanged in the tree
  local bad=0 n=0 mode typ blob path
  while IFS=$'\t' read -r meta path; do
    set -- $meta; blob=$3; n=$((n+1))
    [ -f "$s2/tree_$arm/$path" ] && [ "$(git -C $wt hash-object "$s2/tree_$arm/$path")" = "$blob" ] || { bad=$((bad+1)); echo "tree_$arm MISMATCH $path"; }
  done < <(git -C $wt ls-tree -r $sha)
  echo "tree_$arm verified against $sha: $n files, $bad mismatches"
  [ $bad -eq 0 ]
}
for arm in base fix; do
  if [ $arm = base ]; then sha=$BASE; else sha=$FIX; fi
  if [ -n "$RESUME" ]; then
    verify_tree $arm $sha || { echo "STOP: tree_$arm does not match $sha"; exit 15; }
  else
    mkdir -p "$s2/tree_$arm"
    git -C $wt archive $sha | tar -x -C "$s2/tree_$arm" || { echo "STOP: archive $arm failed"; exit 14; }
    echo "tree_$arm extracted from $sha"
  fi
done
run() { # $1=arm $2=world $3=seed $4=outfile $5=PLAIN|hash|-
  local t=$s2/tree_$1 extra=""; [ "$5" != "-" ] && extra="$5"
  V6_SUBJECT=-1 PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 /usr/bin/time -v -o "$4.time.txt" timeout 3600 bash -c "cd $t && $py $o/hold_spy_v7.py $2 $3 5000 $4 $extra"
}
if [ -n "$RESUME" ]; then  # first: re-run the checker on every existing fix cell (in order); any non-zero stops the resume
  for w_ in frontier_marches crowded_frontier urban_political; do for sd_ in 42 43 44 45 46; do
    if [ -f "$out/fix_${w_}_s${sd_}_v7.json" ] && [ -f "$out/base_${w_}_s${sd_}_v7.json" ]; then
      echo "RESUME recheck fix $w_ s$sd_"; $py $o/stage2_check.py cell "$out/fix_${w_}_s${sd_}_v7.json" "$out/base_${w_}_s${sd_}_v7.json"; rcr=$?
      [ $rcr -ne 0 ] && { echo "STOP: RESUME recheck rc=$rcr on fix $w_ s$sd_"; exit $rcr; }
    fi
  done; done
fi
declare -A PLAIN=( [fix_frontier_marches_43]=1 [fix_crowded_frontier_45]=1 [fix_urban_political_44]=1 [base_crowded_frontier_43]=1 )
for world in frontier_marches crowded_frontier urban_political; do
  for seed in 42 43 44 45 46; do
    for arm in base fix; do
      pin="-"
      cellf="$out/${arm}_${world}_s${seed}_v7.json"; plainf="$out/${arm}_${world}_s${seed}_plain.json"
      if [ -n "$RESUME" ] && [ -f "$cellf" ]; then
        echo "SKIPPED (exists) $arm $world s$seed: $cellf"; [ -n "${PLAIN[${arm}_${world}_${seed}]:-}" ] && { [ -f "$plainf" ] || { echo "STOP: pinned cell exists without its plain twin"; exit 16; }; echo "SKIPPED (exists) plain $arm $world s$seed"; }
        continue
      fi
      if [ -n "${PLAIN[${arm}_${world}_${seed}]:-}" ]; then
        if [ -n "$RESUME" ] && [ -f "$plainf" ]; then echo "SKIPPED (exists) plain $arm $world s$seed: reused"
        else
          check; echo "start plain $arm $world s$seed"
          run $arm $world $seed "$plainf" PLAIN; rc=$?; echo "plain $arm $world s$seed rc=$rc"
          [ $rc -ne 0 ] && { echo "STOP: plain rc=$rc"; exit $rc; }
        fi
        pin=$($py -c "import json;print(json.load(open('$out/${arm}_${world}_s${seed}_plain.json'))['final_hash'])")
        echo "plain $arm $world s$seed hash=$pin"
      fi
      check; echo "start spied $arm $world s$seed pin=$pin"
      run $arm $world $seed "$out/${arm}_${world}_s${seed}_v7.json" "$pin"; rc=$?; echo "spied $arm $world s$seed rc=$rc"
      [ $rc -ne 0 ] && { echo "STOP: spied rc=$rc (3 = hash mismatch = the whole set is void)"; exit $rc; }
      if [ $arm = fix ]; then
        $py $o/stage2_check.py cell "$out/fix_${world}_s${seed}_v7.json" "$out/base_${world}_s${seed}_v7.json"; crc=$?
        [ $crc -ne 0 ] && { echo "STOP: stage2_check cell rc=$crc"; exit $crc; }
      fi
    done
  done
  $py $o/stage2_world_waive.py "$out" $world; wrc=$?
  [ $wrc -ne 0 ] && { echo "STOP: stage2_check world rc=$wrc"; exit $wrc; }
done
exit 0
