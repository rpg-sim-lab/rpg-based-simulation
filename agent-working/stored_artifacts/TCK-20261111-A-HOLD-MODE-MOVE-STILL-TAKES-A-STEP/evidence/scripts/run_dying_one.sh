#!/bin/bash
# ONE-CELL variant of run_dying.sh (needs rpg-planner's approval record id + HOST FREE + the designer's sha OK of every file used). NOT run.
# Usage: ./run_dying_one.sh <arm: fix|base> <seed: 42|43|45>. Anything else is REFUSED (exit 2). Runs exactly that one cell with run_dying.sh's gates, tree verification, pin (the v7 cell's final_hash),
# spy command line, output path and name (dying/cells/<arm>_urban_political_s<seed>_v8.json), so the unchanged run_dying.sh later skips this cell by its existing-output rule. An existing output is skipped, never overwritten.
# Exit 3 = hash mismatch, 4 = spy errors, 10-12 = gates, 15 = tree mismatch, 16 = no pin. Nothing is deleted.
set -u
arm=${1:-}; seed=${2:-}
case "$arm:$seed" in fix:42|fix:43|fix:45|base:42|base:43|base:45) ;; *) echo "REFUSED: usage run_dying_one.sh <fix|base> <42|43|45>"; exit 2;; esac
o=/mnt/data2/rpg-measure/holdmove; s2=$o/stage2; cells=$s2/cells; out=$o/dying/cells; py=/mnt/data/venv-sync2/bin/python
wt=/mnt/data/Working/rpg-based-simulation/.claude/worktrees/holdmove
FIX=b9d78c427280c636d71c67490dda2c8b6c708717; BASE=f94417e6f58f72e0e4289b217df1b0dd9f5bc4e7
mkdir -p "$out"
check() {
  local avail_kb free_kb
  avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo); free_kb=$(df --output=avail -k /mnt/data | tail -1)
  echo "gate: MemAvailable=${avail_kb}kB /mnt/data free=${free_kb}kB $(date -u +%H:%M:%S)"
  if [ "$avail_kb" -lt 3500000 ]; then echo "STOP: MemAvailable ${avail_kb} kB < 3500 MB"; exit 10; fi
  if [ "$free_kb" -lt 3000000 ]; then echo "STOP: /mnt/data free ${free_kb} kB < 3 GB -- tell rpg-planner"; exit 11; fi
  if pgrep -f "[a]rm_child.py|[h]old_spy|[d]ying_window|[p]ytest|[v]3_trace_spy|[d]1_step0_spy" >/dev/null; then echo "STOP: another heavy job is running"; exit 12; fi
}
verify_tree() { # $1=arm $2=sha
  local arm=$1 sha=$2 bad=0 n=0 meta path blob
  while IFS=$'\t' read -r meta path; do
    set -- $meta; blob=$3; n=$((n+1))
    [ -f "$s2/tree_$arm/$path" ] && [ "$(git -C $wt hash-object "$s2/tree_$arm/$path")" = "$blob" ] || { bad=$((bad+1)); echo "tree_$arm MISMATCH $path"; }
  done < <(git -C $wt ls-tree -r $sha)
  echo "tree_$arm verified against $sha: $n files, $bad mismatches"
  [ $bad -eq 0 ]
}
verify_tree fix $FIX || { echo "STOP: tree_fix mismatch"; exit 15; }
verify_tree base $BASE || { echo "STOP: tree_base mismatch"; exit 15; }
cellf="$out/${arm}_urban_political_s${seed}_v8.json"
if [ -f "$cellf" ]; then echo "SKIPPED (exists) $arm s$seed: $cellf"; exit 0; fi
pin=$($py -c "import json;print(json.load(open('$cells/${arm}_urban_political_s${seed}_v7.json'))['final_hash'])") || { echo "STOP: no pin for $arm s$seed"; exit 16; }
t=$s2/tree_$arm
check; echo "start dying $arm urban_political s$seed pin=$pin"
PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 /usr/bin/time -v -o "$cellf.time.txt" timeout 3600 bash -c "cd $t && $py $o/dying_window_v8.py urban_political $seed 5000 $cellf $pin"
rc=$?; echo "dying $arm s$seed rc=$rc"
[ $rc -ne 0 ] && { echo "STOP: rc=$rc (3 = hash mismatch, 4 = spy errors)"; exit $rc; }
exit 0
