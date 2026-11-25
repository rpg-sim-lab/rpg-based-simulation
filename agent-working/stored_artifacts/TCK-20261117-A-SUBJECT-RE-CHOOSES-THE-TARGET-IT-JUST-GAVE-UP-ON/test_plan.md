---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
artifact_type: test_plan
tags: []
---

# Test plan

Written at close (2026-11-22) from the executed evidence of this branch; the ticket was built from the rpg-designer drafts (.claude/handover/drafts/rpg-designer-f2-giveup-memory.md, v2.2 / v2.2a) and rulings relayed by rpg-planner, so no pre-implementation staging artifacts existed.

New tests (mine): tests/unit/strategic/test_propose_target.py, test_giveup_filing.py (edited), test_giveup_clear_and_service.py (37 tests, with failing controls), test_destination_suppression.py; tests/unit/engine/test_propose_target_single_path.py (AST source test; mutants M1-M13 caught), test_notice_suppressed_goal_stands.py, test_objective_destination_suppressed.py; tests/unit/content/test_wayround_settings.py, test_blocker_settings.py; tests/unit/movement/test_giveup_records.py and the oscillation-ladder tests.
Existing tests changed only with the owner's approval (#715 ask 7077660807, answer 7077665927, bound to f2_owner_ask_table_v2.tsv sha 034b11e1): 10 tests in 8 files (commit 59d564c6f).
Executed results: scoped suites strategic / engine / domains-optimization / content / replay / core at the merged head 551f5d09a: all green (647 / 1184 passed, 3 skipped / 141 / 284 / 2 / 424). Health check rc 0 (only the 4 report-only jscpd rows). Measured evidence: spy v10.1 (ccb92ce5) smoke and full runs; the one-off pairing spy v11 (61c4f7cd). Not run: tests/integration and the mutation baselines.

## Proof Plan
- Level: unit tests plus measured own-job runs of the real kernel (smoke 300t, full 3 cells x 5000t, one-off pairing run).
- Proof kind: regression with failing controls (a planted mutant for each rule) and a measured effect (spy v10.1 bars G1-G7, twin hash equal to the plain run).
- Oracle source: the designer's pre-registered bars (draft .claude/handover/drafts/rpg-designer-f2-giveup-memory.md v2.2 / v2.2a) and the owner rulings on #715 (7062303482, 7077665927, 7078467940).
- Expected effect: no stored target and no set target within one tile of a suppressed give-up anchor (G1 / G1-held = 0 except own-tile holds), no record outliving its window (G4 = 0), every place-target write guarded by its value (G6 / G7 = 0). G3 is carried to the D6 ticket.
- Selected commands: `python -m pytest tests/unit/strategic tests/unit/engine tests/unit/domains/optimization tests/unit/content tests/unit/replay tests/unit/core -m "not slow" -n 0`; `python -m codebase.health check`; the approved launcher launch_trace_v10_1_full_b.sh (8cc08c00) for the full run.
