#!/bin/bash
# S2 stored-target measurement. ONE cell at a time. GO file re-checked BEFORE EACH CELL; pauses cleanly when it is gone.
S=/mnt/data2/scratch-b; PY=/mnt/data/scratch-deps-venv/bin/python; GO=$S/st_s2_go
BASE=$S/wt-st-base; FIX=$S/wt-st-fix; O=/mnt/data2/rpg-measure/stored_target_s2; SPY=$S/stored_target_fix_spy.py
SPY_SHA=9b3d3ca8fa3ad6f39636788c878218ea95925764b74780b913225ad682e27ece
OLD=/mnt/data2/rpg-measure/results/cd83111c5-72320cac-5000
mkdir -p $O/base $O/fix $O/plain
ST=$O/status.txt; log() { echo "$(date +%H:%M:%S) $*" >> $ST; }
[ "$(sha256sum $SPY | cut -c1-64)" = "$SPY_SHA" ] || { log SPY_SHA_MISMATCH; exit 1; }
[ "$(sha256sum $FIX/tools/rpg_measure/arm_child.py | cut -c1-16)" = 72320cacb90b3f2b ] || { log CHILD_SHA_MISMATCH; exit 1; }
if ! grep -q IDENTITY $ST 2>/dev/null; then
  n=$(cd $FIX && git diff --name-only cd83111c5 c73d76bad -- src data config tools/rpg_measure tools/test_architecture | wc -l)
  log "IDENTITY c73d76bad vs cd83111c5 on src data config tools/rpg_measure tools/test_architecture: $n differing files (0 = identical; the cd83111c5 fm/crowded s42 plain hashes are valid base twins)"
  log "IDENTITY other tools/ files that differ (not on the run path): $(cd $FIX && git diff --name-only cd83111c5 c73d76bad -- tools | tr '\n' ' ')"
  [ "$n" = 0 ] || { log "IDENTITY_FAILED"; exit 1; }
fi
gate() { # name: GO check + memory bar; returns 1 to stop
  [ -f $GO ] || { log "PAUSED before $1"; return 1; }
  local i av; for i in $(seq 1 30); do av=$(awk '/MemAvailable/{print $2}' /proc/meminfo); [ "$av" -ge 1572864 ] && return 0; sleep 30; [ -f $GO ] || { log "PAUSED before $1 (waiting for memory)"; return 1; }; done
  log "SKIPPED_LOW_MEM before $1 avail_kb=$av"; return 1
}
run() { # tree out args...
  local t=$1; shift; rm -f $S/st_s2_peak.txt; (cd $t && PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=1G -p MemorySwapMax=0 /usr/bin/time -f %M -o $S/st_s2_peak.txt timeout 3000 $PY "$@")
}
clean() { # tree: remove only run dirs this driver's cells create (rpgm_/rpgsfx_ prefixes), by id
  local t=$1 d; for d in $(ls $t/data/runs 2>/dev/null | grep -E '^(rpgm_|rpgsfx_)'); do (cd $t && $PY tools/gate_checks/done_checker_static.py --clean-data-runs --path $d >/dev/null 2>&1); done
}
plain() { # arm tree world
  local out=$O/plain/$1_$3_42.json; [ -s $out ] && return 0
  gate "plain $1 $3 s42" || return 1; local s=$(date +%s)
  run $2 $2/tools/rpg_measure/arm_child.py $3 42 5000 $out > $O/plain/$1_$3_42.log 2>&1; local rc=$?; clean $2
  log "DONE plain $1 $3 s42 rc=$rc peak_rss_kb=$(tail -n 1 $S/st_s2_peak.txt 2>/dev/null) wall=$(( $(date +%s)-s ))s $(grep -o '"final_hash": "[0-9a-f]\{12\}' $out 2>/dev/null | tail -c 13)"
  [ $rc = 0 ] || { log "STOP plain $1 $3 rc=$rc (FAILED cell; if rc is 137/9 or 143 the 1G cap was hit; peak above; no retry at a higher cap without rpg-planner)"; return 1; }
}
spied() { # arm tree world seed
  local out=$O/$1/$3_$4.json; [ -s $out ] && return 0
  gate "spied $1 $3 s$4" || return 1; local s=$(date +%s) twin=""
  if [ $4 = 42 ]; then if [ $1 = base ] && [ $3 != urban_political ]; then twin=$OLD/$3_42.json; else twin=$O/plain/$1_$3_42.json; fi; fi
  run $2 $SPY $3 $4 5000 $out $twin > $O/$1/$3_$4.log 2>&1; local rc=$?; clean $2
  local chk=$($PY $S/st_s2_check.py $out 2>&1 | tail -n 1)
  log "DONE spied $1 $3 s$4 rc=$rc peak_rss_kb=$(tail -n 1 $S/st_s2_peak.txt 2>/dev/null) wall=$(( $(date +%s)-s ))s :: $(tail -n 1 $O/$1/$3_$4.log | cut -c1-200) :: $chk"
  case "$chk" in OK) ;; *) log "STOP spied $1 $3 s$4 :: $chk"; return 1;; esac
  [ $rc = 0 ] || { log "STOP spied $1 $3 s$4 rc=$rc (FAILED cell; if rc is 137/9 or 143 the 1G cap was hit; peak above; no retry at a higher cap without rpg-planner)"; return 1; }
}
plain base $BASE urban_political || exit 0
plain fix $FIX frontier_marches || exit 0
plain fix $FIX crowded_frontier || exit 0
plain fix $FIX urban_political || exit 0
for w in frontier_marches crowded_frontier urban_political; do
  for sd in 42 43 44 45 46; do
    spied base $BASE $w $sd || exit 0
    spied fix $FIX $w $sd || exit 0
  done
  log "WORLD_DONE $w"
done
log ALL_DONE
