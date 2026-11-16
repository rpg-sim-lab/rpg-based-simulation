---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-THE-NON-BLOCKING-REPLAY-TEST-WAITS-A-FIXED-0-7-S-FOR-A-0-5-S-BACKGROUND-WRITE
phase: open
date: 2026-11-16
tags: []
---

# TCK-20261116-THE-NON-BLOCKING-REPLAY-TEST-WAITS-A-FIXED-0-7-S-FOR-A-0-5-S-BACKGROUND-WRITE

## Title
The non-blocking replay test waits a fixed 0.7 s for a 0.5 s background write, so a loaded CI runner fails it

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Filed by rpg-planner on 2026-11-16, from PR #941 (D1) CI run 43864368951, job 133289156607.

`tests/unit/core/test_non_blocking_io.py::test_on_tick_end_is_non_blocking_on_io` failed with `assert 0 == 1 (where 0 = len([]))`:
- the test patches the replay sink's `persist_chunk` to sleep 0.5 s;
- it calls `rm._rotate_chunk`, sleeps a fixed 0.7 s, then asserts `len(rm._manifest["chunks"]) == 1`;
- on a loaded runner the background persist hadn't finished within the 0.2 s margin.

D1's change doesn't touch ReplayManager, and a rerun of the failed job passed. In the last 30 `test.yml` runs on main this test never failed (the one red run, 43715809208, was a different test). So it's a first sighting of a timing-margin flake.

## Scope
1. Replace the fixed sleep with a bounded wait on the condition: poll `rm._manifest["chunks"]` (or join the persist future or executor) up to a generous deadline, e.g. 10 s.
2. Keep the test's claim intact: `_rotate_chunk` returns without waiting for the 0.5 s write, so assert that the call itself returns in well under 0.5 s; and the write lands afterwards.
3. Never weaken the assertion. If the non-blocking claim can't be tested robustly, mark it strict-xfail with this ticket, rather than loosening it.

## Out of Scope
- Any src change to ReplayManager.
- Other timing tests (track them separately if they appear).

## Acceptance Criteria
- The test asserts the call returns in under 0.5 s and that the chunk is recorded within the deadline. With no fixed-sleep margin left, it passes under the 1200 MB RSS ballast and a CPU-loaded runner locally.
- A revert check: making `_rotate_chunk` synchronous fails the test.

## Related Tickets
- TCK-20261116-THE-SEMANTIC-DRIFT-CERTIFICATION-TEST-DOES-NOT-FAIL-ON-A-SLOW-RUNNER (the same class: a wall-clock margin in a test)

## Related Docs
- docs/engine/kernel.md (M7 non-blocking persistence)

## Related Stored Artifacts
None.

## Related Code Areas
- tests/unit/core/test_non_blocking_io.py; src/engine/replay_manager.py (read only)

## Assumptions / Open Questions
- Dispatch is a later owner ask. It's small: testing or an rpg lane.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
