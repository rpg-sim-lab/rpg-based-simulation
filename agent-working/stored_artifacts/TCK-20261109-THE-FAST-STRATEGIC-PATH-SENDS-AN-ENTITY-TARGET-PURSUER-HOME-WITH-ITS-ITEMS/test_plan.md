---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261109-THE-FAST-STRATEGIC-PATH-SENDS-AN-ENTITY-TARGET-PURSUER-HOME-WITH-ITS-ITEMS
artifact_type: test_plan
phase: done
date: 2026-11-11
tags: []
---

# Test plan

Written retroactively at close (2026-11-11). This records the work as done; it was not a pre-implementation artifact.

## Tests
- Row 1 flipped to `test_row1_entity_objective_off_cadence_does_not_regroup_home` (`is None`).
- The strict xfail and its `KNOWN_DISAGREEMENTS` entry for `entity_objective_loaded_entity` removed; `test_the_known_disagreement_table_holds_exactly_row_6` asserts `{"earlier_phase_target_set"}`.
- New wired-path test `tests/unit/strategic/test_pursuit_objective_survives_the_off_cadence_strategic_pass.py`: `AuthoritativeApplyPipeline.refine(state, raw, cadence=OFF_CADENCE)` with `force_full_scan=True`; no REGROUP target and no interaction reset. It failed before the fix (REGROUP to (50,50)). A control without a project still regroups.
- `tests/unit/strategic` (-n 1): 523 passed. `codebase.health check`: 0 worse. mypy gate: rc 0.

## Measurement (pinned runner, PYTHONHASHSEED=0, 5000 ticks)
15 cells: 9 run on this branch's work, 6 base cells reused from main 993400a52 (`git diff 993400a52 2ea0e4d8f -- src data config` is empty). The ticket's own run count reads 16.
- B, c7607b6da, crowded s42: d842c20983d7 (= base).
- Base fliving s45, 2ea0e4d8f: 79205e173df2.
- Fix, c1c762a46: crowded s42 d842c20983d7; s43 21ec90e1e960; s44 361f4a375b81; s45 27112822d9b6; s46 5b1f00924ca5; urban_political s44 4a42776debab; fliving s45 79205e173df2.
All 7 base/fix pairs have identical final hashes and identical result JSONs, so the fix shows in the tests only. Crowded 5-seed deaths 160 to 160 (COMBAT 118, DEFEAT 26, HAZARD 16); extinction check: stop [], base_state [blacksmith, scout], recovered []. rpg-designer ruled PASS with no probe.
