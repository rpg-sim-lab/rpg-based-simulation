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
KIND=${3:-full}   # full = the 12 processes; smoke = NEW, the first world and seed, plain then spy, at SMOKE_TICKS (default 300)
# shellcheck disable=SC1090
. "$ENV_FILE"
TICKS_USED=$TICKS; [ "$KIND" = smoke ] && TICKS_USED=${SMOKE_TICKS:-300}
kitpy() { (cd "$KIT" && PYTHONPATH="$KIT" "$PY" "$@" < /dev/null); }   # EVERY kit python call goes through here (cd $KIT and PYTHONPATH=$KIT), never from the caller's cwd
cell_list() {   # one line per process: "arm world seed mode", in run order
  if [ "$KIND" = smoke ]; then
    for w in $WORLDS; do for sd in $SEEDS; do for mode in plain spy; do echo "new $w $sd $mode"; done; break; done; break; done
  else
    for w in $WORLDS; do for sd in $SEEDS; do for arm in new base; do for mode in plain spy; do echo "$arm $w $sd $mode"; done; done; done; done
  fi
}
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
  SCOPE_CMD=(systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 setsid -w "$PY" -c "$ONE_PROCESS" "$1" "$2" "$3" "$TICKS_USED" "$4" "$tree" "$OUT/cells" "$PY")
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  while read -r arm w sd mode; do scope_command "$arm" "$w" "$sd" "$mode"; echo "SCOPE ${SCOPE_CMD[*]:0:13} <python -c one-process> ${SCOPE_CMD[*]:16}"; done < <(cell_list)
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
disk_ok() {   # disk_ok <label>: 0 when OUT and / each have >= 2 GiB free; otherwise the runner's stop record (disk_floor_stop.json) is written and 1 is returned
  kitpy -c 'import json, sys
from pathlib import Path
from tools.rpg_measure import person_attack_run as r
stop = r.disk_stop(Path(sys.argv[1]), sys.argv[2])
if stop is not None:
    print(json.dumps(stop, sort_keys=True))
sys.exit(0 if stop is None else 1)' "$OUT" "$1" >> "$LOG" 2>&1
}
write_runner_record() {   # <OUT>/runner.json (kitpy: cd $KIT + PYTHONPATH; a failed write returns non-zero)
  kitpy -c 'import sys
from pathlib import Path
from tools.rpg_measure import person_attack_run as r
out, status, freeze_expected, freeze_final, go, ticks, python, worlds, seeds, kind = sys.argv[1:11]
r.write_record(Path(out), status, go, int(ticks), worlds.split(), [int(x) for x in seeds.split()], python, freeze_expected, freeze_final, kind)' "$OUT" "$STATUS" "$FREEZE_SHA" "$FREEZE_FINAL" "$GO" "$TICKS_USED" "$PY" "$WORLDS" "$SEEDS" "$KIND" >> "$LOG" 2>&1
}
finish_record() {   # the runner.json step and its consequence, shared by the run and the control: a record that cannot be written is never COMPLETE
  write_runner_record || { STATUS=RECORD_NOT_WRITTEN; RC=6; echo "RECORD NOT WRITTEN: runner.json could not be written; the run is not COMPLETE" >> "$LOG"; }
}
if [ "${LAUNCH_RECORD_ONLY:-}" = 1 ]; then   # the control: this step alone, from whatever cwd the caller has
  STATUS=${RECORD_STATUS:-COMPLETE}; FREEZE_FINAL=${FREEZE_FINAL_FOR_TEST:-$FREEZE_SHA}; RC=0
  disk_ok "the record-only control"; echo "DISK_CHECK rc=$?" >> "$LOG"
  finish_record; echo "STATUS=$STATUS RC=$RC" >> "$LOG"
  exit "$RC"
fi
pinned_elsewhere() {   # 0 when ANY other process is pinned to cpus 4-5 (perf's obs_cost_arm too): the check is the cpu claim, not a name (pinned_check.py skips this shell's ancestor chain and kernel threads)
  kitpy "$KIT/tools/rpg_measure/pinned_check.py" --cpus 4-5 >> "$LOG" 2>&1; [ $? -ne 0 ]
}
HEAVY_WORDS='tools\.rpg_measure|tools\.test_architecture\.rpg_gate_(harness|run|report)|births_child|coin_boss_spy|births_cost_child|person_attack_(spy|run)'

# --- PREFLIGHT ---
[ -n "$GO" ] || abort "no go reference"
for arm in NEW BASE; do
  tree=$(eval echo "\$TREE_$arm"); sha=$(eval echo "\$SHA_$arm")
  [ -d "$tree" ] || abort "tree $tree missing"
  [ -e "$tree/data/runs" ] && abort "$tree/data/runs already exists: move it out first"
  [ -e "$tree/.git" ] && abort "$tree has a .git: a frozen tree is a git archive, never a checkout"
  kitpy "$KIT/tools/rpg_measure/person_attack_tree_check.py" --repo "$KIT" --sha "$sha" --tree "$tree" >> "$LOG" 2>&1 || abort "tree $tree is not exactly the ls-tree of $sha"
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
pinned_elsewhere && abort "another process is pinned to cpus 4-5 (see PINNED lines above in the log)"
memcheck "the runner"
disk_ok "the start" || abort "disk floor (2 GiB free on OUT and /) crossed before the start"

# --- the 12 processes, ONE AT A TIME, each in its OWN scope, with its own watcher (summed RSS of that child, 2.85 GiB, PAT from the environment), freeze and memory checks around every process ---
export PYTHONDONTWRITEBYTECODE=1   # the children import from the frozen trees: no .pyc may land in them
T0=$(date +%s); echo "RUN START $(date +%T) go=$GO (sequential: one process per scope)" >> "$LOG"
mkdir -p "$OUT/cells"
RC=0; STATUS=COMPLETE; N=0; FREEZE_FINAL=$FREEZE_SHA
while read -r arm w sd mode; do
  [ "$STATUS" = COMPLETE ] || continue
  N=$((N+1)); name="${arm}__${w}__s${sd}__${mode}"
  heavy_running "$HEAVY_WORDS" && abort "another heavy measurement process is running before $name"
  pinned_elsewhere && abort "another process is pinned to cpus 4-5 before $name (see PINNED lines above in the log)"
  memcheck "$name"
  if ! disk_ok "$name"; then STATUS="STOPPED_DISK_FLOOR_BEFORE_$name"; RC=4; echo "STOP: disk floor crossed before $name (see disk_floor_stop.json)" >> "$LOG"; continue; fi
  scope_command "$arm" "$w" "$sd" "$mode"
  PAT='person_attack_spy\.py' "$KIT/tools/rpg_measure/person_attack_watch.sh" "$OUT/watcher_$name.log" < /dev/null &
  WP=$!
  S0=$(date +%s); echo "START $name $(date +%T)" >> "$LOG"
  (cd "$KIT" && PYTHONPATH="$KIT" "${SCOPE_CMD[@]}" >> "$OUT/runner.out" 2>&1 < /dev/null)
  CRC=$?
  echo "END $name rc=$CRC wall=$(( $(date +%s)-S0 ))s $(date +%T)" >> "$LOG"
  wait "$WP" 2>/dev/null
  cur=$(/home/vboxuser/.local/bin/uv pip freeze --python "$PY" 2>/dev/null | sha256sum | cut -c1-64)
  FREEZE_FINAL=$cur
  if [ "$cur" != "$FREEZE_SHA" ]; then STATUS=VOID_INTERPRETER_CHANGED; RC=4; echo "FREEZE CHANGED after $name: STOP (void)" >> "$LOG"; fi
  # rc 0 = clean; 5 / 6 / 7 = a spy cell the kit itself marks invalid (the summarizer says so); anything else (killed by the watcher, a crash, any plain failure) stops the run
  case "$CRC" in 0|5|6|7) ;; *) [ "$STATUS" = COMPLETE ] && { STATUS="STOPPED_AT_$name"; RC=4; echo "STOP: $name returned $CRC" >> "$LOG"; } ;; esac
  if [ "$N" = 1 ] && [ $(( $(date +%s)-T0 )) -gt 1500 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_FIRST_CELL_OVER_25_MIN; RC=4; echo "STOP RULE: the first process took over 25 min" >> "$LOG"; fi
  if [ $(( $(date +%s)-T0 )) -gt 14400 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_OVER_4_H; RC=4; echo "STOP RULE: the run passed 4 h" >> "$LOG"; fi
done < <(cell_list)
finish_record
echo "RUN EXIT $RC status=$STATUS $(date +%T) (wall $(( $(date +%s)-T0 ))s)" >> "$LOG"

# --- the summarizer (offline), then the trees: nothing under data/runs may remain, then the seal LAST ---
if [ "$RC" = 0 ] && [ "$KIND" = full ]; then
  kitpy "$KIT/tools/rpg_measure/person_attack_summary.py" --dir "$OUT/cells" --calendar-tree "$TREE_NEW" --out "$OUT/summary.json" >> "$LOG" 2>&1
  echo "SUMMARY EXIT $? $(date +%T)" >> "$LOG"
fi
for t in "$TREE_NEW" "$TREE_BASE"; do [ -e "$t/data/runs" ] && echo "TREE NOT CLEAN: $t/data/runs exists" >> "$LOG" || echo "TREE CLEAN: $t has no data/runs" >> "$LOG"; done
cd "$OUT" && find . -type f ! -name 'SHA256SUMS*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "SEAL $(sha256sum "$OUT/SHA256SUMS" | cut -c1-64) $(date +%T)" >> "$OUT/SHA256SUMS.seal.log"
exit "$RC"
