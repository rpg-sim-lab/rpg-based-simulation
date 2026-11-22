#!/bin/bash
# NOT RUN by the author. Usage: subject_trace_launch.sh <record.env> <go-reference> <smoke|cells>   (the #715 record id of lead-planner's GO for THIS run)
# The subject trace (Q2), whole: preflight, the subjects derived from the SEALED O3 cells, then the processes ONE AT A TIME (each in its OWN systemd-run scope on cores 4-5), the cell checks, runner.json, the seal LAST.
#   smoke: NEW s42 plain then spy at SMOKE_TICKS (2000), the real-kernel smoke; cells: the four spy cells NEW s42, NEW s45, BASE s42, BASE s45 at TICKS (5000).
# Lesson of TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD: EVERY kit python call goes through kitpy (cd $KIT and PYTHONPATH=$KIT); a record that could not be written makes the run non-COMPLETE with a non-zero RC.
# LAUNCH_DRY_RUN=1 prints the scope commands and exits before the preflight. LAUNCH_RECORD_ONLY=1 runs only the runner.json step (the control that proves it works from a cwd outside the kit).
# <record.env>: KIT, OUT_BASE (the run dir is $OUT_BASE/<smoke|cells>, must not exist), SEALED (the stage-1 cells dir; its parent holds SHA256SUMS and the seal line, which must match before anything starts), TREE_NEW, TREE_BASE, SHA_NEW, SHA_BASE, PY, FREEZE_SHA, WORLD, SEEDS, TICKS, SMOKE_TICKS, and KIT_SHA_<file> for the kit files.
set -u
ENV_FILE=$1
GO=$2
KIND=$3
# shellcheck disable=SC1090
. "$ENV_FILE"
OUT=$OUT_BASE/$KIND
TICKS_USED=$TICKS; [ "$KIND" = smoke ] && TICKS_USED=$SMOKE_TICKS
RUN_SEEDS=$SEEDS   # the seeds the cells run for: after the derivation, only those with at least one subject
seed_args() { SEED_ARGS=(); for sd in $RUN_SEEDS; do SEED_ARGS+=(--seed "$sd"); done; }
seed_args
SMOKE_SEEDS=${SEEDS%% *}
kitpy() { (cd "$KIT" && PYTHONPATH="$KIT" "$PY" "$@" < /dev/null); }   # the ONLY way a kit python call is made
RUNPY=$KIT/tools/rpg_measure/subject_trace_run.py
cell_list() {   # cell_list -> lines "arm seed mode"
  if [ "$KIND" = smoke ]; then echo "new $SMOKE_SEEDS plain"; echo "new $SMOKE_SEEDS spy"
  else for arm in new base; do for sd in $RUN_SEEDS; do echo "$arm $sd spy"; done; done; fi
}
scope_command() {   # scope_command <arm> <seed> <mode>: ONE process in its OWN scope (setsid -w waits for it)
  local tree=$TREE_NEW; [ "$1" = base ] && tree=$TREE_BASE
  SCOPE_CMD=(systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 setsid -w "$PY" "$RUNPY" one --arm "$1" --world "$WORLD" --seed "$2" --ticks "$TICKS_USED" --mode "$3" --tree "$tree" --out "$OUT/cells" --python "$PY" --plan "$OUT/subjects.json")
}
if [ "${LAUNCH_DRY_RUN:-}" = 1 ]; then
  cell_list | while read -r arm sd mode; do scope_command "$arm" "$sd" "$mode"; echo "SCOPE ${SCOPE_CMD[*]}"; done
  exit 0
fi
LOG=$OUT/launcher.log
write_runner_record() {   # the runner.json step: its own function so a control can run it alone
  kitpy "$RUNPY" record --out "$OUT" --status "$STATUS" --go "$GO" --kind "$KIND" --world "$WORLD" "${SEED_ARGS[@]}" --ticks "$TICKS_USED" --python "$PY" --freeze-expected "$FREEZE_SHA" --freeze-final "$FREEZE_FINAL" >> "$LOG" 2>&1
}
disk_ok() {   # disk_ok <label>: 0 when OUT and / each have >= 2 GiB free; otherwise the stop record (disk_floor_stop.json) is written and 1 returned
  kitpy -c 'import json, sys
from pathlib import Path
from tools.rpg_measure import person_attack_run as r
stop = r.disk_stop(Path(sys.argv[1]), sys.argv[2])
if stop is not None:
    print(json.dumps(stop, sort_keys=True))
sys.exit(0 if stop is None else 1)' "$OUT" "$1" >> "$LOG" 2>&1
}
finish_record() {   # the runner.json step and its consequence, shared by the real run and the control: a record that cannot be written is never COMPLETE
  write_runner_record || { STATUS=RECORD_NOT_WRITTEN; RC=6; echo "RECORD NOT WRITTEN: runner.json could not be written; the run is not COMPLETE" >> "$LOG"; }
}
if [ "${LAUNCH_RECORD_ONLY:-}" = 1 ]; then
  STATUS=${RECORD_STATUS:-COMPLETE}; FREEZE_FINAL=${FREEZE_FINAL_FOR_TEST:-$FREEZE_SHA}; RC=0; mkdir -p "$OUT"
  disk_ok "the record-only control"; echo "DISK_CHECK rc=$?" >> "$LOG"   # a kit python -c call from the caller's cwd
  finish_record; echo "STATUS=$STATUS RC=$RC" >> "$LOG"
  exit "$RC"
fi
mkdir -p "$OUT"
abort() { echo "ABORT: $1 $(date +%T)" >> "$LOG"; exit 3; }
memcheck() { local a; a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3145728 ] || abort "MemAvailable ${a} kB < 3 GiB before $1"; }
heavy_running() {   # the self-match-proof check: argv SHAPE (an interpreter then -m <module> or a <script>.py), this shell's ancestor chain skipped
  local words=$1 chain=" $$ " p=$$ pid args
  while [ "${p:-0}" -gt 1 ]; do p=$(ps -o ppid= -p "$p" 2>/dev/null | tr -d ' '); [ -n "$p" ] && chain="$chain$p "; done
  while read -r pid args; do
    case "$chain" in *" $pid "*) continue ;; esac
    if echo "$args" | command grep -Eq "^[^ ]*python[0-9.]*( +-[A-Za-z]+)* +-m +($words)( |$)|^[^ ]*python[0-9.]*( +-[A-Za-z]+)* +[^ ]*($words)[^ ]*\.py( |$)"; then return 0; fi
  done < <(ps -ww -eo pid=,args=)
  return 1
}
pinned_elsewhere() {   # 0 when ANY other process is pinned to cpus 4-5 (perf's obs_cost_arm too): the check is the cpu claim, not a name; it skips this shell's ancestor chain and kernel threads (pinned_check.py)
  kitpy "$KIT/tools/rpg_measure/pinned_check.py" --cpus 4-5 >> "$LOG" 2>&1; [ $? -ne 0 ]
}
HEAVY_WORDS='tools\.rpg_measure|tools\.test_architecture\.rpg_gate_(harness|run|report)|births_child|coin_boss_spy|births_cost_child|person_attack_(spy|run)|subject_trace_(spy|run)'

# --- PREFLIGHT ---
[ -n "$GO" ] || abort "no go reference"
kitpy "$RUNPY" seal-check --dir "$SEALED/.." >> "$LOG" 2>&1 || abort "the stage-1 seal does not match: sha256(SHA256SUMS) differs from its SEAL line (stage 2 refuses to start)"
[ "$KIND" = smoke ] || [ "$KIND" = cells ] || abort "kind must be smoke or cells"
if [ "$KIND" != smoke ]; then   # the stage-1 cells must have been written by the approved stage-1 spy: its kit_sha256_after_run.txt (beside the stage-1 OUT) names that spy sha256
  AFTER_RUN="$SEALED/../../kit_sha256_after_run.txt"
  { [ -f "$AFTER_RUN" ] && command grep -q "^${KIT_SHA_person_attack_spy_py}  tools/rpg_measure/person_attack_spy.py" "$AFTER_RUN"; } || abort "kit_sha256_after_run.txt of the stage-1 run does not name the stage-1 spy ${KIT_SHA_person_attack_spy_py:0:8}: the cells are not from the approved spy (not judged)"
fi
for arm in NEW BASE; do
  tree=$(eval echo "\$TREE_$arm"); sha=$(eval echo "\$SHA_$arm")
  [ -d "$tree" ] || abort "tree $tree missing"
  [ -e "$tree/data/runs" ] && abort "$tree/data/runs already exists: move it out first"
  [ -e "$tree/.git" ] && abort "$tree has a .git: a frozen tree is a git archive, never a checkout"
  kitpy "$KIT/tools/rpg_measure/person_attack_tree_check.py" --repo "$KIT" --sha "$sha" --tree "$tree" >> "$LOG" 2>&1 || abort "tree $tree is not exactly the ls-tree of $sha"
  echo "TREE $arm $sha ($tree): equal to git ls-tree, no data/runs" >> "$LOG"
done
FREEZE_FINAL=$(/home/vboxuser/.local/bin/uv pip freeze --python "$PY" 2>/dev/null | sha256sum | cut -c1-64)
[ "$FREEZE_FINAL" = "$FREEZE_SHA" ] || abort "interpreter freeze sha256 $FREEZE_FINAL differs from the record $FREEZE_SHA"
for f in subject_trace_spy.py subject_trace_run.py person_attack_spy.py person_attack_summary.py person_attack_run.py person_attack_tree_check.py person_attack_watch.sh arm_child.py; do
  var="KIT_SHA_${f//[.]/_}"; want=${!var:-}
  [ -n "$want" ] || abort "no recorded sha256 for $f"
  [ "$(sha256sum "$KIT/tools/rpg_measure/$f" | cut -c1-64)" = "$want" ] || abort "$f sha256 differs from the record"
done
[ -d "$SEALED" ] || abort "the sealed O3 cells dir is missing"
(cd "$SEALED/.." && sha256sum -c SHA256SUMS --quiet >> "$LOG" 2>&1) || abort "the sealed O3 run no longer matches its SHA256SUMS"
heavy_running "$HEAVY_WORDS" && abort "another heavy measurement process is running"
pinned_elsewhere && abort "another process is pinned to cpus 4-5 (see PINNED lines above in the log)"
memcheck "the runner"
disk_ok "the start" || abort "disk floor (2 GiB free on OUT and /) crossed before the start"
mkdir -p "$OUT/cells"
kitpy "$RUNPY" derive --sealed "$SEALED" --world "$WORLD" "${SEED_ARGS[@]}" --out "$OUT/subjects.json" >> "$LOG" 2>&1 || abort "the subject list could not be derived from the sealed cells"
echo "SUBJECTS sha256 $(sha256sum "$OUT/subjects.json" | cut -c1-64) (written and hashed before the first stage-2 process)" | tee "$OUT/subjects.json.sha256" >> "$LOG"
if [ "$KIND" = cells ]; then
  RUN_SEEDS=$(kitpy "$RUNPY" seeds --plan "$OUT/subjects.json") || abort "could not read the seeds with subjects"
  [ -n "$RUN_SEEDS" ] || abort "no seed has a subject: nothing to run"
  seed_args
  echo "CELLS for seeds with a subject: $RUN_SEEDS (NEW and the same-seed BASE)" >> "$LOG"
fi

# --- the processes, ONE AT A TIME, each in its OWN scope with its own watcher, freeze and memory checks around every process ---
export PYTHONDONTWRITEBYTECODE=1   # the children import from the frozen trees: no .pyc may land in them
T0=$(date +%s); echo "RUN START $(date +%T) go=$GO kind=$KIND (sequential: one process per scope)" >> "$LOG"
RC=0; STATUS=COMPLETE; N=0
while read -r arm sd mode; do
  [ "$STATUS" = COMPLETE ] || continue
  N=$((N+1)); name="${arm}__${WORLD}__s${sd}__${mode}"
  heavy_running "$HEAVY_WORDS" && abort "another heavy measurement process is running before $name"
  pinned_elsewhere && abort "another process is pinned to cpus 4-5 before $name (see PINNED lines above in the log)"
  memcheck "$name"
  if ! disk_ok "$name"; then STATUS="STOPPED_DISK_FLOOR_BEFORE_$name"; RC=4; echo "STOP: disk floor crossed before $name (see disk_floor_stop.json)" >> "$LOG"; continue; fi
  scope_command "$arm" "$sd" "$mode"
  PAT='subject_trace_spy\.py' "$KIT/tools/rpg_measure/person_attack_watch.sh" "$OUT/watcher_$name.log" < /dev/null &
  WP=$!
  P0=$(date +%s); echo "START $name $(date +%T)" >> "$LOG"
  (cd "$KIT" && PYTHONPATH="$KIT" "${SCOPE_CMD[@]}" >> "$OUT/runner.out" 2>&1 < /dev/null)
  CRC=$?
  echo "END $name rc=$CRC wall=$(( $(date +%s)-P0 ))s $(date +%T)" >> "$LOG"   # the process's OWN time (P0); the stop rules below use the run's start T0 on purpose
  wait "$WP" 2>/dev/null
  FREEZE_FINAL=$(/home/vboxuser/.local/bin/uv pip freeze --python "$PY" 2>/dev/null | sha256sum | cut -c1-64)
  if [ "$FREEZE_FINAL" != "$FREEZE_SHA" ]; then STATUS=VOID_INTERPRETER_CHANGED; RC=4; echo "FREEZE CHANGED after $name: STOP (void)" >> "$LOG"; fi
  # rc 0 = clean; 8 = a spy exception (the cell is void and the check says so); anything else (a kill, a crash) stops the run
  case "$CRC" in 0|8) ;; *) [ "$STATUS" = COMPLETE ] && { STATUS="STOPPED_AT_$name"; RC=4; echo "STOP: $name returned $CRC" >> "$LOG"; } ;; esac
  if [ "$N" = 1 ] && [ $(( $(date +%s)-T0 )) -gt 1500 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_FIRST_PROCESS_OVER_25_MIN; RC=4; echo "STOP RULE: the first process took over 25 min (checked after it ended)" >> "$LOG"; fi
  if [ $(( $(date +%s)-T0 )) -gt 7200 ] && [ "$STATUS" = COMPLETE ]; then STATUS=STOPPED_OVER_2_H; RC=4; echo "STOP RULE: the run passed 2 h (checked after a process ended)" >> "$LOG"; fi
done < <(cell_list)

# --- the checks and the record: a failure here is never COMPLETE ---
if [ "$STATUS" = COMPLETE ] && [ "$KIND" = cells ]; then
  kitpy "$RUNPY" check --cells "$OUT/cells" --sealed "$SEALED" --world "$WORLD" "${SEED_ARGS[@]}" --ticks "$TICKS_USED" --out "$OUT/cell_validity.json" >> "$LOG" 2>&1 || { STATUS=COMPLETE_WITH_VOID_CELLS; RC=1; echo "CHECK: at least one cell is void (see cell_validity.json)" >> "$LOG"; }
fi
finish_record
echo "RUN EXIT $RC status=$STATUS $(date +%T) (wall $(( $(date +%s)-T0 ))s)" >> "$LOG"
for t in "$TREE_NEW" "$TREE_BASE"; do [ -e "$t/data/runs" ] && echo "TREE NOT CLEAN: $t/data/runs exists" >> "$LOG" || echo "TREE CLEAN: $t has no data/runs" >> "$LOG"; done
cd "$OUT" && find . -type f ! -name 'SHA256SUMS*' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
echo "SEAL $(sha256sum "$OUT/SHA256SUMS" | cut -c1-64) $(date +%T)" >> "$OUT/SHA256SUMS.seal.log"
exit "$RC"
