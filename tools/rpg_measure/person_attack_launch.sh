#!/bin/bash
# NOT RUN by the author. Usage: person_attack_launch.sh <record.env> <go-reference>   (the #715 record id of lead-planner's GO for THIS record set)
# The person-attack trace, whole: preflight (nothing heavy before it passes), the runner under the slot, the summarizer, the tree-clean proof, the seal LAST.
# <record.env> is the record set's own shell-variable file (written once, before the seal, never edited after it): KIT (kit checkout), OUT, TREE_NEW, TREE_BASE, SHA_NEW, SHA_BASE, PY, FREEZE_SHA,
# WORLDS, SEEDS, TICKS, and the kit file sha256s as KIT_SHA_<name>. The kit words live only in this file and the record set, never on a launcher's command line.
set -u
ENV_FILE=$1
GO=$2
# shellcheck disable=SC1090
. "$ENV_FILE"
LOG=$OUT/launcher.log
mkdir -p "$OUT"
abort() { echo "ABORT: $1 $(date +%T)" >> "$LOG"; exit 3; }
memcheck() { local a; a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3145728 ] || abort "MemAvailable ${a} kB < 3 GiB before $1"; }

# --- the self-match-proof heavy check (kit-notes/heavy_check_self_match.md): argv SHAPE (an interpreter then -m <module> or a <script>.py) and skip this shell's ancestor chain ---
heavy_running() {   # heavy_running '<script regex>' -> 0 when another process RUNS such a script, 1 otherwise
  local words=$1 chain=" $$ " p=$$ pid args
  while [ "${p:-0}" -gt 1 ]; do p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$p" ] && chain="$chain$p "; done
  while read -r pid args; do
    case "$chain" in *" $pid "*) continue ;; esac
    if echo "$args" | command grep -Eq "^[^ ]*python[0-9.]*( +-[A-Za-z]+)* +-m +($words)( |$)|^[^ ]*python[0-9.]*( +-[A-Za-z]+)* +[^ ]*($words)[^ ]*\.py( |$)"; then return 0; fi
  done < <(ps -ww -eo pid=,args=)
  return 1
}
HEAVY_WORDS='tools\.rpg_measure|tools\.test_architecture\.rpg_gate_(harness|run|report)|births_child|coin_boss_spy|births_cost_child|person_attack_(spy|run)'

# --- PREFLIGHT ---
[ -n "$GO" ] || abort "no go reference"
for arm in NEW BASE; do
  tree=$(eval echo "\$TREE_$arm"); sha=$(eval echo "\$SHA_$arm")
  [ -d "$tree" ] || abort "tree $tree missing"
  [ -e "$tree/data/runs" ] && abort "$tree/data/runs already exists: move it out first"
  [ -e "$tree/.git" ] && abort "$tree has a .git: a frozen tree is a git archive, never a checkout"
  "$PY" "$KIT/tools/rpg_measure/person_attack_tree_check.py" --repo "$KIT" --sha "$sha" --tree "$tree" >> "$LOG" 2>&1 || abort "tree $tree is not exactly the ls-tree of $sha"
  echo "TREE $arm $sha ($tree): equal to git ls-tree (paths and blob hashes), no data/runs" >> "$LOG"
done
cur=$(/home/vboxuser/.local/bin/uv pip freeze --python "$PY" 2>/dev/null | sha256sum | cut -c1-64)
[ "$cur" = "$FREEZE_SHA" ] || abort "interpreter freeze sha256 $cur differs from the record $FREEZE_SHA"
for f in person_attack_spy.py person_attack_summary.py person_attack_run.py person_attack_tree_check.py person_attack_watch.sh arm_child.py; do
  var="KIT_SHA_${f//[.]/_}"; want=${!var:-}
  [ -n "$want" ] || abort "no recorded sha256 for $f"
  [ "$(sha256sum "$KIT/tools/rpg_measure/$f" | cut -c1-64)" = "$want" ] || abort "$f sha256 differs from the record"
done
heavy_running "$HEAVY_WORDS" && abort "another heavy measurement process is running"
memcheck "the runner"

# --- the runner, under the slot, with the watcher (summed RSS of the children, 2.85 GiB, reads PAT from the environment) ---
T0=$(date +%s); echo "RUN START $(date +%T) go=$GO" >> "$LOG"
ARGS=(--out "$OUT/cells" --go "$GO" --ticks "$TICKS" --python "$PY" --tree "new=$TREE_NEW" --tree "base=$TREE_BASE")
for w in $WORLDS; do ARGS+=(--world "$w"); done
for s in $SEEDS; do ARGS+=(--seed "$s"); done
PAT='person_attack_spy\.py' "$KIT/tools/rpg_measure/person_attack_watch.sh" "$OUT/watcher.log" &
WP=$!
cd "$KIT" && PYTHONPATH="$KIT" systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 setsid "$PY" "$KIT/tools/rpg_measure/person_attack_run.py" "${ARGS[@]}" >> "$OUT/runner.out" 2>&1
RC=$?
echo "RUN EXIT $RC $(date +%T) (wall $(( $(date +%s)-T0 ))s)" >> "$LOG"
wait "$WP" 2>/dev/null

# --- the summarizer (offline), then the trees: nothing under data/runs may remain, then the seal LAST ---
if [ "$RC" = 0 ]; then
  "$PY" "$KIT/tools/rpg_measure/person_attack_summary.py" --dir "$OUT/cells" --calendar-tree "$TREE_NEW" --out "$OUT/summary.json" >> "$LOG" 2>&1
  echo "SUMMARY EXIT $? $(date +%T)" >> "$LOG"
fi
for t in "$TREE_NEW" "$TREE_BASE"; do [ -e "$t/data/runs" ] && echo "TREE NOT CLEAN: $t/data/runs exists" >> "$LOG" || echo "TREE CLEAN: $t has no data/runs" >> "$LOG"; done
cd "$OUT" && find . -type f ! -name 'SHA256SUMS*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "SEAL $(sha256sum "$OUT/SHA256SUMS" | cut -c1-64) $(date +%T)" >> "$OUT/SHA256SUMS.seal.log"
