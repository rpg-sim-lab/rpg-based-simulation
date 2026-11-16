---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20261115-SWEEP-RUN-INDEX-BUILDER-CANNOT-BE-CALLED-ON-ITS-OWN
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-SWEEP-RUN-INDEX-BUILDER-CANNOT-BE-CALLED-ON-ITS-OWN

## Title
The sweep's run-index builder is inline in ScenarioSweeper.run_sweep, so "the index survives a freshly corrupted run" can no longer be tested

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
Found by platform-implementer during the world farm (TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING, follow-up 13590ffe0); handed to rpg by platform-planner, 2026-11-15. The index builder is inline in `ScenarioSweeper.run_sweep` (src/observability/sweeper.py, about l.281-335). tests/unit/observability/test_run_index_builder.py's second step re-ran the same sweep id to regenerate the index after corrupting one run. The world farm now refuses a reused id, so that step asserts the refusal instead, and the check that the index builder survives a freshly corrupted run is lost. The farm ticket carries it as a limits line.

## Scope
1. Extract the index build into a function callable on an existing sweep dir, with run_sweep calling it, and behaviour byte-identical (the same index files for the same inputs).
2. Restore the lost check: build a sweep, corrupt one run (manifest and report removed), call the builder alone, and assert the index the old test asserted.

## Out of Scope
Changing the index format, or the world farm's refuse rule.

## Acceptance Criteria
1. The builder is callable alone, and run_sweep's output is unchanged (an existing sweep test's files are compared before and after).
2. test_run_index_builder.py again asserts that the builder survives a freshly corrupted run, plus the refusal it asserts now.
3. Scoped tests pass (tests/unit+integration/observability).

## Related Tickets
TCK-20261115-WORLD-FARM-RUNS-WORLDS-SIDE-BY-SIDE-WITHOUT-CLASHING (limits line).

## Related Docs
docs/simulation/lab_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
src/observability/sweeper.py; tests/unit/observability/test_run_index_builder.py

## Assumptions / Open Questions
Lands after the world farm merges.

## Implementation Notes
Small: one extraction plus one test. Unscheduled; dispatch needs a go.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
