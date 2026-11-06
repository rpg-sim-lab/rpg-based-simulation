---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-07
tags: []
---

# combined_run: two measurement scripts (rpg-planner-ubuntu, 2026-11-07)

- `percause_check.py` (sha256 083f9b356103...): per-cause death bar over `tools/rpg_measure/arm_child.py` results, same ruler as `paired.py`; reads `<cache>/results/<sha12>-<child>-<ticks>/<world>_<seed>.json`, exit 2 (REFUSED) on a missing cell.
- `starv_trace.py` (sha256 6e373af4fc02...): per-tick trace of named entities in one cell, built exactly like `arm_child.py`; prints `MATCH` or `MISMATCH` against the cell's `final_hash` (exit 0 or 3), death rows with the typed cause, and `V3_RECORD_MISSING` when a traced id starved without a recorder record.
- Positive control of `starv_trace.py`: tree 3533fde7135b, crowded_frontier s42 1000t, ids 30 1 10: `MATCH 8259e502ae16 vs cell 8259e502ae16`, death rows e10 COMBAT t471 and e1 HAZARD t528 (2026-11-07).
- Run both from the arm's `git archive` tree with `PYTHONHASHSEED=0` and `PYTHONPATH` set to that tree; the scripts are copied byte-identical from the measurement host's scratch.
