#!/bin/bash
# TCK-20261110 measurement, 22 runs, ONE AT A TIME. Does nothing unless the GO file exists (rpg-planner's HOST FREE). No pytest anywhere.
S=/mnt/data2/scratch-b; M=$S/nonflight_meas; PY=/mnt/data/scratch-deps-venv/bin/python; R=/mnt/data2/rpg-measure/results
BASE=$S/wt-5c6990e51; FIX=$S/wt-824483949
SPY=$FIX/agent-working/staging_artifacts/TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING/held_step_spy.py
SPY_SHA=84e7811388fb8345abe006caf127f54a288e78aa5fd8c9603ea6757edbc4125d
CHILD_SHA=72320cacb90b3f2b
BASE_OUT=$R/5c6990e51c2c-72320cac-5000-nonflight   # lane C's 5c6990e51c2c-72320cac-5000 is left alone
FIX_OUT=$R/824483949cec-72320cac-5000
mkdir -p $BASE_OUT $FIX_OUT
[ -f $M/GO ] || { echo "NO GO FILE: not started" >&2; exit 1; }
note() { echo "$*" >> $M/progress.txt; }
one() { # tree script-args... : runs python in the tree, 3G cap, 3000 s timeout
  local t=$1; shift
  (cd $t && PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout 3000 $PY "$@")
}
plain() { # name tree outdir world seed
  [ "$(sha256sum $2/tools/rpg_measure/arm_child.py | cut -c1-16)" = "$CHILD_SHA" ] || { note "CHILD_SHA_MISMATCH $1"; return; }
  local s=$(date +%s); one $2 $2/tools/rpg_measure/arm_child.py $4 $5 5000 $3/$4_$5.json > $M/$1.log 2>&1
  note "DONE $1 rc=$? wall=$(( $(date +%s)-s ))s"
}
spied() { # name world seed
  [ "$(sha256sum $SPY | cut -c1-64)" = "$SPY_SHA" ] || { note "SPY_SHA_MISMATCH $1"; return; }
  local s=$(date +%s); one $FIX $SPY $2 $3 5000 $FIX_OUT/spy_$2_$3.json > $M/$1.log 2>&1
  note "DONE $1 rc=$? wall=$(( $(date +%s)-s ))s $(tail -1 $M/$1.log)"
}
# v2 (rpg-designer ruling): base cells are done (10 files exist); plain fix s42 twins FIRST, then the spied cells that are missing.
check_pins() { # json: new stop rule. Records every pin >= 50; STOP on (i) >=500, (ii) held at the last tick (>=4999), (iii) a held subject dies in [first, last+1] (hp fell to 0); hp for a pin past the first 40 held_rows is NOT in the spy output.
  $PY - "$1" <<'PYEOF'
import json,sys
d=json.load(open(sys.argv[1])); stop=[]
for p in d["runs_ge_50"]:
    e=str(p["entity"]); a=p["first_tick"]; b=a+p["ticks"]-1
    print("PIN", sys.argv[1].split("/")[-1], p)
    if p["ticks"]>=500: stop.append(("i",p))
    if b>=4999: stop.append(("ii",p))
    dt=d["death"].get(e)
    if dt and dt[0] is not None and a<=dt[0]<=b+1: stop.append(("iii-death",p,dt))
    hr=[r for r in d["held_rows"] if str(r["subject"])==e]
    if len(hr)>1 and hr[-1]["hp"]<hr[0]["hp"]: stop.append(("iii-hp-first40",p))
print("PINSTOP" if stop else "PINS_OK", sys.argv[1].split("/")[-1], stop)
PYEOF
}
for w in crowded_frontier urban_political; do plain fixplain_${w}_42 $FIX $FIX_OUT $w 42; done
plain fixplain_crowded_frontier_43 $FIX $FIX_OUT crowded_frontier 43
$PY - <<PYEOF >> $M/progress.txt
import json
a=json.load(open("$FIX_OUT/spy_crowded_frontier_42.json"))["final_hash"]; b=json.load(open("$FIX_OUT/crowded_frontier_42.json"))["final_hash"]
print("HASHCHECK crowded s42 spied", a[:12], "plain", b[:12], "MATCH" if a==b else "MISMATCH")
PYEOF
grep -q "HASHCHECK crowded s42.* MATCH" $M/progress.txt || { note "STOP_HASH_MISMATCH spied rows void"; exit 1; }
$PY - <<PYEOF >> $M/progress.txt
import json
a=json.load(open("$FIX_OUT/spy_crowded_frontier_43.json"))["final_hash"]; b=json.load(open("$FIX_OUT/crowded_frontier_43.json"))["final_hash"]
print("HASHCHECK crowded s43 spied", a[:12], "plain", b[:12], "MATCH" if a==b else "MISMATCH")
PYEOF
grep -q "HASHCHECK crowded s43.* MATCH" $M/progress.txt || { note "STOP_HASH_MISMATCH s43 spied rows void"; exit 1; }
for f in spy_crowded_frontier_42 spy_crowded_frontier_43; do check_pins $FIX_OUT/$f.json >> $M/progress.txt; done
for c in "crowded_frontier 44" "crowded_frontier 45" "crowded_frontier 46" "urban_political 42" "urban_political 43" "urban_political 44" "urban_political 45" "urban_political 46"; do
  set -- $c; spied spy_$1_$2 $1 $2
  check_pins $FIX_OUT/spy_$1_$2.json >> $M/progress.txt
  tail -1 $M/progress.txt | grep -q PINSTOP && { note "STOP_PIN"; exit 1; }
done
$PY - <<PYEOF >> $M/progress.txt
import json
a=json.load(open("$FIX_OUT/spy_urban_political_42.json"))["final_hash"]; b=json.load(open("$FIX_OUT/urban_political_42.json"))["final_hash"]
print("HASHCHECK urban s42 spied", a[:12], "plain", b[:12], "MATCH" if a==b else "MISMATCH")
PYEOF
note ALL_DONE
