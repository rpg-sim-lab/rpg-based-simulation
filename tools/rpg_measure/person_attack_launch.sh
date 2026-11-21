#!/bin/bash
# NOT RUN by the author. Usage: person_attack_launch.sh <record.env> <go-reference>   (the #715 record id of lead-planner's GO for THIS record set)
# The person-attack trace, whole: preflight (nothing heavy before it passes), then the 12 processes ONE AT A TIME (each in its OWN systemd-run scope), the summarizer, the tree-clean proof, the seal LAST.
# Sequential: for each world, seed, arm (new then base) the PLAIN twin, then the SPY; each process is one call of person_attack_run.run_child (the runner's own function, run.py is untouched) inside its own 3G scope on cores 4-5.
# LAUNCH_DRY_RUN=1 prints the 12 scope command lines in order and exits before the preflight (no process, no log).
# <record.env> is the record set's own shell-variable file (written once, before the seal, never edited after it): KIT (kit checkout), OUT, TREE_NEW, TREE_BASE, SHA_NEW, SHA_BASE, PY, FREEZE_SHA,
# WORLDS, SEEDS, TICKS, and the kit file sha256s as KIT_SHA_<name>. The kit words live only in this file and the record set, never on a launcher's command line.
set -u
ENV_FILE=$1
GO=$2
# shellcheck disable=SC1090
. "$ENV_FILE"
ONE_PROCESS='import json, sys
from pathlib import Path
from tools.rpg_measure import person_attack_run as r
arm, world, seed, ticks, mode, tree, out, python = sys.argv[1:9]
item = {"arm": arm, "world": world, "seed": int(seed), "ticks": int(ticks), "mode": mode, "name": r.cell_name(arm, world, int(seed), mode)}
result = r.run_child(python, Path(tree), Path(out), item)
print(json.dumps(result, sort_keys=True))
sys.exit(result["returncode"])'
scope_command() {   # scope_command <arm> <world> <seed> <mode>: ONE process in its OWN scope (setsid -w waits for it)
  local tree=$TREE_NEW; [ "$1" = base ] && tree=$TREE_BASE
  SCOPE_CMD=(systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 setsid -w "$PY" -c "$ONE_PROCESS" "$1" "$2" "$3" "$TICKS" "$4" "$tree" "$OUT/cells" "$PY")
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  for w in $WORLDS; do for sd in $SEEDS; do for arm in new base; do for mode in plain spy; do scope_command "$arm" "$w" "$sd" "$mode"; echo "SCOPE ${SCOPE_CMD[*]:0:13} <python -c one-process> ${SCOPE_CMD[*]:16}"; done; done; done; done
  exit 0
fi
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

# --- the 12 processes, ONE AT A TIME, each in its OWN scope, with its own watcher (summed RSS of that child, 2.85 GiB, PAT from the environment), freeze and memory checks around every process ---
export PYTHONDONTWRITEBYTECODE=1   # the children import from the frozen trees: no .pyc may land in them
T0=$(date +%s); echo "RUN START $(date +%T) go=$GO (sequential: one process per scope)" >> "$LOG"
mkdir -p "$OUT/cells"
RC=0; STATUS=COMPLETE; N=0
for w in $WORLDS; do for sd in $SEEDS; do for arm in new base; do for mode in plain spy; do
  [ "$STATUS" = COMPLETE ] || continue
  N=$((N+1)); name="${arm}__${w}__s${sd}__${mode}"
  heavy_running "$HEAVY_WORDS" && abort "another heavy measurement process is running before $name"
  memcheck "$name"
  scope_command "$arm" "$w" "$sd" "$mode"
  PAT='person_attack_spy\.py' "$KIT/tools/rpg_measure/person_attack_watch.sh" "$OUT/watcher_$name.log" &
  WP=$!
  S0=$(date +%s); echo "START $name $(date +%T)" >> "$LOG"
  (cd "$KIT" && PYTHONPATH="$KIT" "${SCOPE_CMD[@]}" >> "$OUT/runner.out" 2>&1)
  CRC=$?
  echo "END $name rc=$CRC wall=$(( $(date +%s)-S0 ))s $(date +%T)" >> "$LOG"
  wait "$WP" 2>/dev/null
  cur=$(/home/vboxuser/.local/bin/uv pip freeze --python "$PY" 2>/dev/null | sha256sum | cut -c1-64)
  if [ "$cur" != "$FREEZE_SHA" ]; then STATUS=VOID_INTERPRETER_CHANGED; RC=4; echo "FREEZE CHANGED after $name: STOP (void)" >> "$LOG"; fi
  # rc 0 = clean; 5 / 6 / 7 = a spy cell the kit itself marks invalid (the summarizer says so); anything else (killed by the watcher, a crash, any plain failure) stops the run
  case "$CRC" in 0|5|6|7) ;; *) [ "$STATUS" = COMPLETE ] && { STATUS="STOPPED_AT_$name"; RC=4; echo "STOP: $name returned $CRC" >> "$LOG"; } ;; esac
  if [ "$N" = 1 ] && [ $(( $(date +%s)-T0 )) -gt 1500 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_FIRST_CELL_OVER_25_MIN; RC=4; echo "STOP RULE: the first process took over 25 min" >> "$LOG"; fi
  if [ $(( $(date +%s)-T0 )) -gt 14400 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_OVER_4_H; RC=4; echo "STOP RULE: the run passed 4 h" >> "$LOG"; fi
done; done; done; done
"$PY" -c 'import json, sys
from pathlib import Path
from tools.rpg_measure import person_attack_run as r
out, status, freeze, go, ticks, py = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), sys.argv[6]
worlds, seeds = sys.argv[7].split(), [int(x) for x in sys.argv[8].split()]
items = r.plan(["new", "base"], worlds, seeds, ticks)
codes = {i["name"]: json.loads((out / (i["name"] + ".exit.json")).read_text())["returncode"] if (out / (i["name"] + ".exit.json")).exists() else None for i in items}
(out / "runner.json").write_text(json.dumps({"go": go, "mode": "sequential, one process per scope", "ticks": ticks, "worlds": worlds, "seeds": seeds, "python": py, "freeze_sha_expected": freeze, "status": status, "returncodes": codes, "twin_equal": r.twin_check(out, items)}, indent=2, sort_keys=True))' "$OUT/cells" "$STATUS" "$FREEZE_SHA" "$GO" "$TICKS" "$PY" "$WORLDS" "$SEEDS" >> "$LOG" 2>&1
echo "RUN EXIT $RC status=$STATUS $(date +%T) (wall $(( $(date +%s)-T0 ))s)" >> "$LOG"

# --- the summarizer (offline), then the trees: nothing under data/runs may remain, then the seal LAST ---
if [ "$RC" = 0 ]; then
  "$PY" "$KIT/tools/rpg_measure/person_attack_summary.py" --dir "$OUT/cells" --calendar-tree "$TREE_NEW" --out "$OUT/summary.json" >> "$LOG" 2>&1
  echo "SUMMARY EXIT $? $(date +%T)" >> "$LOG"
fi
for t in "$TREE_NEW" "$TREE_BASE"; do [ -e "$t/data/runs" ] && echo "TREE NOT CLEAN: $t/data/runs exists" >> "$LOG" || echo "TREE CLEAN: $t has no data/runs" >> "$LOG"; done
cd "$OUT" && find . -type f ! -name 'SHA256SUMS*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "SEAL $(sha256sum "$OUT/SHA256SUMS" | cut -c1-64) $(date +%T)" >> "$OUT/SHA256SUMS.seal.log"
