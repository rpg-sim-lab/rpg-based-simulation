---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE
phase: open
date: 2026-11-01
tags: [performance]
---

# TCK-20261101-PERF-BENCH-KNOWN-REDS-PARKED-DURING-THE-PAUSE

## Title
Own the perf bench and arena stress known reds while most perf work is paused

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Five entries in `tools/test_architecture/slow_known_reds.yaml` cite TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP, which is in done/, with owner `rpg-implementer-2`. The owner paused most perf work until an RPG milestone (#715 issuecomment-6556861718) and chose "Reword, skip arena smoke" for these entries (#715 issuecomment-6556925036): perf-planner writes reasons naming the pause, testing-planner edits the file. lead-planner named perf-planner as owner of the entries, and testing-planner repoints them here.

This ticket is the open home for those entries. It is not a plan to make the tests green during the pause.

## Scope
- Hold the reason text below for the five entries. testing-planner applies it to the file.
- `test_arena_stress_50v50`: name the failing check, once the owner says whether that is exempt from the pause. Route any code fix to the owner of that code.
- When the pause lifts, or by each entry's `expires_on`, decide per entry: fix, re-date or delete. Expiry forces that decision, so it is not extended here.

## Out of Scope
- Editing `slow_known_reds.yaml` (testing-planner).
- `tests.integration.certification.test_catalog_arena_smoke::test_catalog_arena_small_can_tick`: outside the pause, owned by rpg-planner under its own ticket.
- Any perf run, threshold change or test edit during the pause.

## Acceptance Criteria
- [ ] The five entries cite this ticket, name `perf-planner` as owner, and carry the reason text below.
- [ ] The failing check of `test_arena_stress_50v50` is named, with evidence from a run or a clearer assertion message, and the entry's reason text is updated to match.
- [ ] Each entry has been fixed, deliberately re-dated with the owner's decision, or deleted, and this ticket records which.

## Reason Text
Each is one `note:` value. `expires_on` stays as it is today (2026-12-31 on all five). `added_on` is unchanged.

- `tests.perf.test_perf_movement*`, `tests.perf.test_perf_passive_scaling*`, `tests.perf.test_perf_strategic*`:
  `"parked under the owner's perf pause until an RPG milestone (#715 6556861718, 6556925036); first allowed during core RPG + perf core implementation (owner, 2026-10-07)"`
- `tests.perf.test_perf_combat::test_perf_combat*`:
  `"parked under the owner's perf pause until an RPG milestone (#715 6556861718, 6556925036); first red run 37682076933 at a514e2025 (range 6e7ef56ec..a514e2025 incl. #407); cause not attributed"`
- `tests.arena.test_arena_stress::test_arena_stress_50v50`:
  `"parked, cause not attributed, reads as a conformance failure, not peak RSS (test source read, not run; #715 6556925036); first red run 37682076933 at a514e2025 (range 6e7ef56ec..a514e2025 incl. #407)"`

## Related Tickets
- TCK-20261006-COMBAT-ENGAGEMENT-HOSTILITY-PROJECTION-COST-STEP (the done ticket these entries cited)
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (known-reds reporting)

## Related Docs
- docs/engine/performance_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/slow_known_reds.yaml` (testing-planner applies edits)
- `tests/perf/test_perf_movement*`, `test_perf_passive_scaling*`, `test_perf_strategic*`, `test_perf_combat*`
- `tests/arena/test_arena_stress.py` (not a perf-owned path; tracked here only)
- `tests/tools/perf_assertions.py`

## Assumptions / Open Questions
- Open, with the owner via lead-planner: is naming the failing check of `test_arena_stress_50v50` exempt from the pause? Do not run it until answered.
- The conformance reading comes from source at origin/main, not a run. The test has two checks: line 26 `assert result.conformance_passed`, and line 44 `assert_perf_threshold(result.peak_rss_mb, 375.0, ...)` with `hard` at its default False, which warns with the value and limit rather than failing. Run 41230865672 at e523f92b2 shows only `assert False` (as relayed by testing-planner via lead-planner-u24; log not read by perf-planner). Whether a warnings-as-errors setting applies was not checked. It may be a real bug rather than a perf cost, which the pause keeps open.
- The causes of the four `tests.perf.*` reds are not established by this ticket.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
