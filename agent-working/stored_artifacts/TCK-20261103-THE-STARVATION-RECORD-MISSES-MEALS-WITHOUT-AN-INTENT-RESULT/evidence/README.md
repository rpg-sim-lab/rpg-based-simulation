---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT
artifact_type: investigation
---

# Evidence: crowded_frontier s45, base vs fix

- Wrapper: `arm_child_starv.py`, sha256 e6d87053438d85a9382e476e1e51c65145aef22547bcc51f4bfae885b564b6d5. It is tools/rpg_measure/arm_child.py plus three copy-out hunks (a constant, `_starvation(run_dir)`, one key `starvation_events` in the result); it copies the starvation events out before the run dir is removed.
- Cell: `PYTHONHASHSEED=0 PYTHONPATH=$t systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 timeout 1800 /mnt/data/venv-sync2/bin/python arm_child_starv.py crowded_frontier 45 5000 <out>`, cwd = an extracted git archive.
- Base e755dc3d1 (tree 2a462fe43455a866911d4f1be15d00b1e5f25a33), fix ba05f8c01 (tree df7d0fe36c6fe0b28c7304fb9463828c476e4e9a); src equals the closing head's src.
- End hash, both arms: 2209d09642c0d93d15ee376238f96cd1d14395d1f4cc6b234e67994053b34e76 = lane C's arm_child base cell. Hash-equal.
- e31 (hero, starved t2439): last_meal_tick None -> 810; ways attempted [] -> []; UNTRIED_STEP -> UNTRIED_STEP.
- e37 (raider): alive at 5000t in both arms, no record.
- Not re-read: e30 (crowded s42), e9 (crowded s46), e53 (frontier_living_world s45).
- Full result JSONs stay under /mnt/data2/rpg-measure/recorder/results (sha256 of each in crowded_frontier_45_records.json); the records extract is in this folder.
