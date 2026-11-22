---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-TRACE-KIT-CALENDAR-LOAD-WRITES-BYTECODE-INTO-A-FROZEN-TREE

## Title
The trace kit's calendar loader writes a .pyc into the frozen tree it reads, when it is called outside the launcher

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/rpg_measure/person_attack_summary.py::load_is_night` loads a frozen tree's `src/core/calendar.py`
by file path through importlib. Called from an ad-hoc python without `PYTHONDONTWRITEBYTECODE`, it
wrote `src/core/__pycache__/calendar.cpython-313.pyc` into the frozen NEW tree
`/data/vboxuser/o3-trace-trees/87792e3e8ec42dfd0015f745bbcc5077262bb17d` at 2026-11-22 11:32:33
(rpg-implementer-ubuntu's read of the sealed O3 cells during the Q2 build). The kit's own launched
processes were clean, because the launchers export `PYTHONDONTWRITEBYTECODE=1`. The next smoke's
preflight tree check then aborted (smoke 1 of kit bb32b19b2, GO #715 7074481677, 11:58:50, "DIFFERS (1)").
Lead-planner restored the tree by moving the file to
`/data/vboxuser/o3-trace-runs/quarantine-87792e3e8-pyc-20261122/` (decision #715 7074493947). The sealed
O3 run is unaffected: its trees were EQUAL at its start and the file postdates its seal.

## Scope
- Make every kit function that loads code from a frozen tree immune to the caller's environment: set
  `sys.dont_write_bytecode = True` around the load (restoring the previous value), or load the source
  without the import system's cache.
- A control: call `load_is_night` on a temporary tree with bytecode writing switched ON in the
  environment, and assert that no `__pycache__` appears.

## Out of Scope
- The approved kit heads (cd3a76430, bb32b19b2): the fix lands on the next kit only.
- The quarantined file: it stays where lead-planner moved it.

## Acceptance Criteria
1. `load_is_night` on a tree leaves the tree byte-identical, whatever `PYTHONDONTWRITEBYTECODE` is set to.
2. The new control fails on the current loader and passes on the fixed one.

## Related Tickets
- TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES
- TCK-20261122-PERSON-ATTACK-LAUNCHER-WRITES-NO-RUNNER-RECORD

## Related Docs
- tools/rpg_measure/person_attack_kit_note.md

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261121-MEAT-EATERS-IN-FRONTIER-LIVING-WORLD-ATTACK-PEOPLE-FORTY-TIMES-MORE-AFTER-THE-NIGHT-AND-SLOT-FIXES/rpg_designer_o3_kit_answers_2026-11-21.md

## Related Code Areas
- tools/rpg_measure/person_attack_summary.py
- tests/tools/test_person_attack_kit.py

## Assumptions / Open Questions
- Ad-hoc reads of frozen trees also run with `PYTHONDONTWRITEBYTECODE=1` and `python -B` from now on;
  this ticket removes the reliance on that habit.

## Implementation Notes
- Also fold into the same next-kit change (found in smoke 2 of kit 39859549b, 2026-11-22): `subject_trace_launch.sh:124` logs each process's END `wall=` as `now - T0` (the run's start), not the process's own time, so the second process reads wall=170s against 85.6 s in run_times.log. Cosmetic; the stop rules use T0 on purpose and are unaffected.
- Also fold in (rpg-designer's answer (b), relayed by lead-planner 2026-11-22): the `MotiveReads` class docstring in `tools/rpg_measure/person_attack_spy.py` (spy d3cb7072 at 39859549b, lines 90-93) says "``source`` is never passed", but the code passes `source_identity(entity)` and records it per row as `relation_source` / `relation_source_default`. Docstring-only; it stays as it is in the approved spy and is corrected in the next kit.
- Also fold in (found 2026-11-22 before stage 2, lead-planner asked): the launchers' heavy-process check (`subject_trace_launch.sh:59-68` `heavy_running` / `HEAVY_WORDS`, and the same list in `person_attack_launch.sh`) names only RPG-measure modules, so it does not catch perf-planner's `/data/vboxuser/perf_runs/obs_kit/obs_cost_arm.py` on cpus 4-5 (its own regex tested on live pids 973826/973827: NOT caught). Next kit: also refuse when any other process is pinned to the measurement cpus, or add the perf kit's scripts to the list. Stage 2 relies on the GO's "no obs_cost_arm process" condition instead.

## Test Summary

## Files Changed

## Completion Summary
