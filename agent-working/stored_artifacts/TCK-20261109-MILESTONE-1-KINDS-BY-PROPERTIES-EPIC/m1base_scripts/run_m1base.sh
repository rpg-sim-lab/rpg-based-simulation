#!/bin/bash
# M1-base record: fill the paired cache (events kept), then paired.py unchanged over the cache with --collected (executes nothing).
set -u
BASE=/mnt/data2/rpg-measure/m1base
TOOL=/mnt/data/Working/rpg-based-simulation
PY=/mnt/data/venv-sync2/bin/python
SHA=9c398a068d3899e56c11a3b805d07f5c71bd8217
cd $TOOL || exit 8
$PY $BASE/fill_cache.py || { echo "STOP: fill_cache rc=$?"; exit 6; }
$PY -m tools.rpg_measure.paired --base $SHA --new $SHA --report-only --seeds 42 43 44 45 46 --self-check seed42 --collected "$($PY -c 'from tools.rpg_measure import paired; print(paired.resolve_cache())')" --out $BASE/table.md --verdict-json $BASE/verdict.json
rc=$?
echo "paired rc=$rc"; cat $BASE/verdict.json
[ $rc -eq 0 ] && grep -q '"outcome": "PASS"' $BASE/verdict.json || { echo "STOP: paired not PASS"; exit 4; }
