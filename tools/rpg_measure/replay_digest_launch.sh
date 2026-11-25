#!/bin/bash
# NOT RUN by the author. NEW is the sha of the branch's code commit (76732f456...): the NEW tree is a git archive of THAT commit, not of the branch head (the branch head also carries this kit and monitoring rows).
# The replay-bytes comparison for the per-tick digest memo (TCK-20261124-THE-PER-TICK-REPLAY-DIGEST-WALKS-THE-WHOLE-STATE-EVERY-TICK, AC2).
# Usage: replay_digest_launch.sh dry                 trees, checks and the printed commands; NO simulation process
#        replay_digest_launch.sh run <go-reference>  the 4 processes (the #715 record id of lead-planner's GO for this run set)
# Step 0 (before the 4): a second BASE frontier_living_world s42 101-tick smoke into OUT/step0, compared with the first smoke's chunk_0000 under the frozen mask. Not equal masked (or equal unmasked) = VOID "key list incomplete" and NO AC2 process starts.
# 4 processes, ONE AT A TIME, each in its OWN systemd-run scope (3G, no swap), on cpus 4-5 under taskset, cwd = a frozen git-archive tree, PYTHONDONTWRITEBYTECODE=1 and python -B, replay ON, audit_mode:
#   for each world (frontier_living_world s42, then crowded_frontier s42): NEW (the branch) then BASE (the merge base), 2000 ticks.
# Refuses to start (and before every process) while any other process is pinned to cpus 4-5 (obs_cost_arm included): the check reads the cpus a process is allowed on, not its name.
# VOID on: a tree that differs from `git ls-tree -r`, a non-zero exit, a missing chunk or final hash, chunk counts that differ between the arms (replay_digest_compare.py). Nothing is deleted: run dirs are MOVED out
# of the trees; a seal (SHA256SUMS) is written LAST and nothing is edited after it.
set -u
MODE=${1:-}
GO=${2:-}
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=${REPLAY_DIGEST_REPO:-$(cd "$HERE/../.." && pwd)}
PY=${REPLAY_DIGEST_PY:-/data/vboxuser/Work/rpg-based-simulation/.venv/bin/python}
NEW_SHA=${REPLAY_DIGEST_NEW:-76732f45626238f766a5bc1ca6ddf34ca53b073c}
BASE_SHA=${REPLAY_DIGEST_BASE:-36a7e2089ec1115c311edd8a15b4394c27664bd6}   # the merge base of NEW and origin/main (b99b1e2d1 merged 36a7e2089)
WORLDS=${REPLAY_DIGEST_WORLDS:-"frontier_living_world crowded_frontier"}
SEED=42
TICKS=${REPLAY_DIGEST_TICKS:-2000}
CONTEXT_PREFIX=c12afb16a10d   # perf's reference final hash for frontier_living_world s42 at 613a8365bcd1: context only
CPUS=4-5
NEW_FULL=$(git -C "$REPO" rev-parse "$NEW_SHA^{commit}" 2>/dev/null) || { echo "ABORT: $NEW_SHA is not a commit in $REPO"; exit 3; }
BASE_FULL=$(git -C "$REPO" rev-parse "$BASE_SHA^{commit}" 2>/dev/null) || { echo "ABORT: $BASE_SHA is not a commit in $REPO"; exit 3; }
ROOT=${REPLAY_DIGEST_ROOT:-/data/vboxuser/replay-digest-runs/$NEW_FULL}
TREE_NEW=$ROOT/trees/$NEW_FULL
TREE_BASE=$ROOT/trees/$BASE_FULL
OUT=$ROOT/out
LOG=$OUT/launcher.log
ARM=$HERE/replay_digest_arm.py
CMP=$HERE/replay_digest_compare.py
KEYS=$HERE/replay_digest_wall_clock_keys.jsonl   # the frozen wall-clock leaf list: pinned by sha256 below, copied into OUT, nothing added after the run
KEYS_SHA256=${REPLAY_DIGEST_KEYS_SHA256:-0c6fe7cf3986979c8c3bb4d4872573e2c0c4689c78f21f6bd055ba804bacd52c}
STEP0_TICKS=101
SMOKE_CHUNK=${REPLAY_DIGEST_SMOKE_CHUNK:-/data/vboxuser/replay-digest-smoke/36a7e2089/out/rundir/chunk_0000.json}   # a chunk BASE itself produced (the dry check): the preflight positive control runs on a copy of it
TREECHECK=$HERE/person_attack_tree_check.py
case "$MODE" in dry) ;; run) [ -n "$GO" ] || { echo "ABORT: run needs the GO reference"; exit 3; } ;; *) echo "usage: $0 dry | run <go-reference>"; exit 2 ;; esac
[ -f "$ARM" ] && [ -f "$CMP" ] && [ -f "$TREECHECK" ] && [ -f "$KEYS" ] || { echo "ABORT: a kit file is missing under $HERE"; exit 3; }

say() { echo "$*"; [ -d "$OUT" ] && echo "$*" >> "$LOG"; return 0; }
abort() { echo "ABORT: $1 $(date +%T)"; [ -d "$OUT" ] && echo "ABORT: $1 $(date +%T)" >> "$LOG"; exit 3; }
void() { echo "VOID: $1" >> "$OUT/VOID_REASONS"; say "VOID: $1"; }

# --- other processes pinned to the measurement cpus: the checker's own ancestor chain, kernel threads and empty command lines are skipped ---
pinned_elsewhere() {
  "$PY" -I -B - "$CPUS" <<'PYEOF'
import os, sys
def cpus(text):
    s = set()
    for part in text.strip().split(","):
        if part:
            lo, _, hi = part.partition("-")
            s.update(range(int(lo), int(hi or lo) + 1))
    return s
want = cpus(sys.argv[1])
machine = cpus(open("/sys/devices/system/cpu/online").read())
def status(pid):
    d = {}
    for line in open(f"/proc/{pid}/status", errors="replace").read().splitlines():
        k, _, v = line.partition(":"); d[k] = v.strip()
    return d
own, p = set(), os.getpid()
while p and p > 1 and p not in own:
    own.add(p)
    try: p = int(status(p).get("PPid", "0"))
    except OSError: break
found = []
for name in sorted((n for n in os.listdir("/proc") if n.isdigit()), key=int):
    pid = int(name)
    if pid in own or pid == 2: continue
    try:
        st = status(pid); args = open(f"/proc/{pid}/cmdline", "rb").read().replace(b"\0", b" ").decode("utf-8", "replace").strip()
    except OSError: continue
    if not args or st.get("PPid") == "2": continue
    allowed = cpus(st.get("Cpus_allowed_list", ""))
    if allowed and allowed != machine and allowed & want:
        found.append(f"PINNED pid={pid} cpus={st.get('Cpus_allowed_list')} {args[:160]}")
print("\n".join(found))
sys.exit(1 if found else 0)
PYEOF
}

make_tree() {   # make_tree <sha> <tree>: a fresh git archive when the tree is not there yet (never into an existing one)
  if [ ! -e "$2" ]; then mkdir -p "$2" && git -C "$REPO" archive "$1" | tar -x -C "$2" || abort "git archive of $1 failed"; fi
}
check_tree() {  # check_tree <sha> <tree>: EXACTLY git ls-tree -r (paths and blob hashes), no data/runs
  "$PY" -I -B "$TREECHECK" --repo "$REPO" --sha "$1" --tree "$2" > "$2.check.txt" 2>&1
  local rc=$?
  [ -e "$2/data/runs" ] && { echo "data/runs exists in the tree" >> "$2.check.txt"; rc=1; }
  return $rc
}
cell_list() { for w in $WORLDS; do echo "new $w"; echo "base $w"; done; }
tree_of() { [ "$1" = new ] && echo "$TREE_NEW" || echo "$TREE_BASE"; }
scope_command() {   # scope_command <arm> <world>: the ONE process
  local tree; tree=$(tree_of "$1")
  SCOPE_CMD=(systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c "$CPUS" setsid -w env "PYTHONDONTWRITEBYTECODE=1" "PYTHONHASHSEED=0" "TMPDIR=$ROOT/tmp" "$PY" -B "$ARM" "$2" "$SEED" "$TICKS" "$OUT/cells/$1_$2.json")
}

keys_ok() { [ "$(sha256sum "$KEYS" | cut -d' ' -f1)" = "$KEYS_SHA256" ]; }
control() {   # control <chunk> <label>: the positive control; exit 0 when every expectation holds
  "$PY" -I -B "$CMP" control "$1" "$KEYS" > "${CONTROL_OUT:-/dev/null}.$2.json" 2>&1
}

# ---------------------------------------------------------------- dry
if [ "$MODE" = dry ]; then
  mkdir -p "$ROOT/trees" "$ROOT/tmp"
  echo "DRY RUN (no simulation process). NEW=$NEW_FULL BASE=$BASE_FULL ROOT=$ROOT cpus=$CPUS ticks=$TICKS seed=$SEED worlds=[$WORLDS] python=$PY"
  make_tree "$NEW_FULL" "$TREE_NEW"; make_tree "$BASE_FULL" "$TREE_BASE"
  for pair in "$NEW_FULL $TREE_NEW" "$BASE_FULL $TREE_BASE"; do set -- $pair; if check_tree "$1" "$2"; then echo "TREE $2: equal to git ls-tree -r $1, no data/runs"; else echo "TREE $2 DIFFERS (VOID):"; head -5 "$2.check.txt"; fi; done
  if out=$(pinned_elsewhere); then echo "PINNED CHECK: no other process is pinned to cpus $CPUS"; else echo "PINNED CHECK: REFUSES (a real run would stop here):"; echo "$out"; fi
  if keys_ok; then echo "KEYS: $KEYS sha256 equals the pinned $KEYS_SHA256"; else echo "KEYS: $KEYS sha256 DIFFERS from the pinned $KEYS_SHA256 (a real run would stop here)"; fi
  if [ -f "$SMOKE_CHUNK" ]; then
    if "$PY" -I -B "$CMP" control "$SMOKE_CHUNK" "$KEYS" > "$ROOT/tmp/control_dry.json" 2>&1; then echo "POSITIVE CONTROL on $SMOKE_CHUNK: ok ($(tr -d '\n ' < "$ROOT/tmp/control_dry.json" | grep -o '"reading":"[^"]*"'))"; else echo "POSITIVE CONTROL FAILED (see $ROOT/tmp/control_dry.json)"; fi
  else echo "POSITIVE CONTROL: smoke chunk $SMOKE_CHUNK not found (a real run would stop here)"; fi
  echo "MemAvailable: $(awk '/MemAvailable/{print $2}' /proc/meminfo) kB (a run needs >= 3145728); free on /data: $(df -BG --output=avail /data | tail -1 | tr -d ' ')"
  while read -r arm w; do
    scope_command "$arm" "$w"
    echo "CELL $arm $w: cd $(tree_of "$arm") && ${SCOPE_CMD[*]}"
  done < <(cell_list)
  echo "STEP 0: cd $TREE_BASE && systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c $CPUS setsid -w env PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 TMPDIR=$ROOT/tmp $PY -B $ARM frontier_living_world $SEED $STEP0_TICKS $OUT/step0/base_frontier_101.json ; then: python -B $CMP pair $SMOKE_CHUNK $OUT/step0/rundir/chunk_0000.json $KEYS $OUT/step0/pair.json (equal masked AND different unmasked, else VOID key list incomplete, no AC2 process)"
  echo "AFTER EACH PROCESS: the exit code goes to $OUT/cells/<arm>_<world>.rc, the run dir <tree>/data/runs/rd_<world>_$SEED is MOVED to $OUT/rundirs/<arm>_<world> and the tree must have no data/runs"
  echo "AFTER ALL: both trees re-checked against ls-tree; positive control on this run's own chunk; python -B $CMP compare $OUT $KEYS <worlds> --context-prefix $CONTEXT_PREFIX > compare.md/json; run_times.log; SHA256SUMS last"
  exit 0
fi

# ---------------------------------------------------------------- run
[ -e "$OUT" ] && { echo "ABORT: $OUT exists: one record per directory; move it out first"; exit 3; }
mkdir -p "$OUT/cells" "$OUT/rundirs" "$ROOT/tmp" "$ROOT/trees"
say "START $(date -Is) GO=$GO NEW=$NEW_FULL BASE=$BASE_FULL cpus=$CPUS ticks=$TICKS seed=$SEED worlds=[$WORLDS] python=$PY"
memcheck() { local a; a=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$a" -ge 3145728 ] || abort "MemAvailable ${a} kB < 3 GiB before $1"; }
diskcheck() { local g; g=$(df -BG --output=avail /data | tail -1 | tr -d 'G '); [ "$g" -ge 4 ] || abort "less than 4 GiB free on /data before $1"; }
if ! out=$(pinned_elsewhere); then say "$out"; abort "another process is pinned to cpus $CPUS"; fi
diskcheck preflight; memcheck preflight
keys_ok || abort "$KEYS sha256 differs from the pinned $KEYS_SHA256: the key list is frozen"
cp "$KEYS" "$OUT/wall_clock_keys.frozen.json"
[ -f "$SMOKE_CHUNK" ] || abort "the smoke chunk $SMOKE_CHUNK (a BASE chunk, for the positive control) is missing"
"$PY" -I -B "$CMP" control "$SMOKE_CHUNK" "$KEYS" > "$OUT/control_before.json" 2>&1 || { void "positive control failed before the run (control_before.json)"; abort "positive control failed"; }
say "POSITIVE CONTROL before the run: ok (control_before.json)"
make_tree "$NEW_FULL" "$TREE_NEW"; make_tree "$BASE_FULL" "$TREE_BASE"
for pair in "$NEW_FULL $TREE_NEW" "$BASE_FULL $TREE_BASE"; do
  set -- $pair
  if check_tree "$1" "$2"; then say "TREE $2: equal to git ls-tree -r $1, no data/runs"; else cp "$2.check.txt" "$OUT/tree_check_$(basename "$2").txt"; void "tree $2 differs from git ls-tree -r $1"; abort "tree check failed"; fi
done
: > "$OUT/run_times.log"
RC_ALL=0
# --- step 0: the completeness proof of the key list, before any AC2 process ---
mkdir -p "$OUT/step0"
if ! out=$(pinned_elsewhere); then say "$out"; abort "another process is pinned to cpus $CPUS before step 0"; fi
memcheck "step 0"; diskcheck "step 0"
SCOPE_CMD=(systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c "$CPUS" setsid -w env "PYTHONDONTWRITEBYTECODE=1" "PYTHONHASHSEED=0" "TMPDIR=$ROOT/tmp" "$PY" -B "$ARM" frontier_living_world "$SEED" "$STEP0_TICKS" "$OUT/step0/base_frontier_101.json")
say "STEP 0 START $(date +%T): ${SCOPE_CMD[*]}"; t0=$(date +%s)
(cd "$TREE_BASE" && "${SCOPE_CMD[@]}" < /dev/null > "$OUT/step0/stdout.txt" 2> "$OUT/step0/stderr.txt"); rc=$?; t1=$(date +%s)
echo "step0 frontier_living_world rc=$rc wall_s=$((t1 - t0))" >> "$OUT/run_times.log"; say "STEP 0 END rc=$rc wall=$((t1 - t0))s"
[ -d "$TREE_BASE/data/runs/rd_frontier_living_world_$SEED" ] && mv "$TREE_BASE/data/runs/rd_frontier_living_world_$SEED" "$OUT/step0/rundir"
if [ -d "$TREE_BASE/data/runs" ]; then for left in "$TREE_BASE"/data/runs/*; do [ -e "$left" ] && mv "$left" "$OUT/step0/extra_$(basename "$left")"; done; rmdir "$TREE_BASE/data/runs" 2>/dev/null; rmdir "$TREE_BASE/data" 2>/dev/null; fi
if [ "$rc" != 0 ] || [ ! -f "$OUT/step0/rundir/chunk_0000.json" ]; then void "step 0 smoke failed (rc=$rc) or produced no chunk_0000"; abort "step 0 failed: no AC2 process starts"; fi
if "$PY" -I -B "$CMP" pair "$SMOKE_CHUNK" "$OUT/step0/rundir/chunk_0000.json" "$KEYS" "$OUT/step0/pair.json" > "$OUT/step0/pair.stdout" 2>&1; then say "STEP 0: the second BASE smoke equals the first under the frozen mask and differs without it: the key list is complete for this chunk"
else void "key list incomplete (or a meaningless control): see step0/pair.json (differing leaves)"; abort "step 0 failed: no AC2 process starts"; fi
if check_tree "$BASE_FULL" "$TREE_BASE"; then say "TREE AFTER STEP 0 $TREE_BASE: equal to git ls-tree -r, no data/runs"; else void "BASE tree differs from ls-tree after step 0"; abort "tree check failed after step 0"; fi
while read -r arm w; do
  if ! out=$(pinned_elsewhere); then say "$out"; abort "another process is pinned to cpus $CPUS before $arm $w"; fi
  memcheck "$arm $w"; diskcheck "$arm $w"
  tree=$(tree_of "$arm"); scope_command "$arm" "$w"
  say "CELL $arm $w: START $(date +%T): ${SCOPE_CMD[*]}"
  t0=$(date +%s)
  (cd "$tree" && "${SCOPE_CMD[@]}" < /dev/null > "$OUT/cells/${arm}_${w}.stdout" 2> "$OUT/cells/${arm}_${w}.stderr"); rc=$?
  t1=$(date +%s)
  echo "$rc" > "$OUT/cells/${arm}_${w}.rc"
  echo "$arm $w rc=$rc wall_s=$((t1 - t0)) start=$t0 end=$t1" >> "$OUT/run_times.log"
  say "CELL $arm $w: END rc=$rc wall=$((t1 - t0))s"
  [ "$rc" = 0 ] || { RC_ALL=1; void "$arm $w exited $rc"; }
  rd="$tree/data/runs/rd_${w}_${SEED}"
  if [ -d "$rd" ]; then mv "$rd" "$OUT/rundirs/${arm}_${w}" || void "could not move $rd"; else void "$arm $w: no run directory $rd"; fi
  # anything else left under data/runs is moved too (never deleted), so the tree stays clean
  if [ -d "$tree/data/runs" ]; then
    for left in "$tree"/data/runs/*; do [ -e "$left" ] && mv "$left" "$OUT/rundirs/${arm}_${w}__extra_$(basename "$left")" && say "MOVED extra run dir $left"; done
    rmdir "$tree/data/runs" 2>/dev/null; rmdir "$tree/data" 2>/dev/null
  fi
done < <(cell_list)

# --- after: the trees must still be exactly ls-tree, then the compare, then the seal LAST ---
for pair in "$NEW_FULL $TREE_NEW" "$BASE_FULL $TREE_BASE"; do
  set -- $pair
  if check_tree "$1" "$2"; then say "TREE AFTER $2: equal to git ls-tree -r $1, no data/runs"; else cp "$2.check.txt" "$OUT/tree_check_after_$(basename "$2").txt"; void "tree $2 differs from ls-tree AFTER the run"; fi
done
first_chunk=$(ls "$OUT"/rundirs/new_*/chunk_0000.json 2>/dev/null | head -1)
if [ -n "$first_chunk" ] && "$PY" -I -B "$CMP" control "$first_chunk" "$KEYS" > "$OUT/control_after.json" 2>&1; then say "POSITIVE CONTROL on this run's own NEW chunk, before the compare: ok (control_after.json)"; else void "positive control failed on this run's chunk (control_after.json)"; fi
"$PY" -I -B "$CMP" compare "$OUT" "$KEYS" $WORLDS --context-prefix "$CONTEXT_PREFIX" >> "$LOG" 2>&1; CMP_RC=$?
[ -s "$OUT/VOID_REASONS" ] && say "RESULT: VOID (see VOID_REASONS)" || { [ "$CMP_RC" = 0 ] && say "RESULT: PASS (replay bytes equal)" || say "RESULT: FAIL (a difference; see compare.md)"; }
say "END $(date -Is)"
( cd "$OUT" && find . -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS ) && echo "SEALED $(sha256sum "$OUT/SHA256SUMS" | cut -c1-16)"
exit $((RC_ALL | CMP_RC))
