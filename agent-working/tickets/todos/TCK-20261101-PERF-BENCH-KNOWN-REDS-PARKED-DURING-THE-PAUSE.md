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
  `"parked, cause not attributed; a conformance failure, not peak RSS (line 26 in run 41230865672), check not named, passed alone locally 2026-11-01 (#715 6557042733); first red run 37682076933 at a514e2025 (range 6e7ef56ec..a514e2025 incl. #407)"`

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
- Open: how to name the failing check of `test_arena_stress_50v50`. The owner's exemption (#715 6557042733) covered one local run, now spent, and it did not name the check. Any next step needs a new decision.
- It may be a real bug rather than a perf cost, which the pause keeps open.
- The causes of the four `tests.perf.*` reds are not established by this ticket.

## Implementation Notes
**`test_arena_stress_50v50`, one exempted run, 2026-11-01 (#715 6557042733): PASSED, so the failing check is NOT named.**
- Local: `systemd-run --user --scope -q -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5 .venv/bin/python -m pytest tests/arena/test_arena_stress.py::test_arena_stress_50v50 --resource-budget large -vv -s`, the test alone in its process, at f8e05dc87 (origin/main code plus tickets), Python 3.13.7, 67.57 s. Certification PASS, hash status MATCHED, peak RSS 122.1 MB, tick compute about 50-81 ms in the ticks the report shows. One run, no retry.
- CI: run 41230865672 at e523f92b2, JUnit from the `slow-junit` artifact. It failed twice in that run (`slow_tests.xml` 64.2 s, `legacy_regression.xml` 63.8 s), both at line 26 `assert result.conformance_passed`, so this is the conformance assertion and not the peak RSS one. pytest's repr is cut in the middle, so `failure_kind` and `failure_reason` are not in the JUnit. The `certification-report` artifact covers only IDLE_CLEAN and RAM_PRESSURE, not this scenario.
- What the visible part of the CI repr shows (`legacy_regression.xml`, ticks 1-2 only): `memory_rss_mb` 351.5 against the local 103.0 at tick 1, and `tick_compute_ms` 34-36. The test's profile has `max_ram_mb=512` and `max_tick_budget_ms=400` (limit 600 with the 1.5 burst). The CI runs share a process with the rest of the slow suite, so the local run did not reproduce that condition.
- Unproven candidates, in `src/certification/conformance.py` order: a RAM envelope breach (the higher starting RSS leaves about 160 MB, and the local run grew about 19 MB over 50 ticks, which is not enough on its own); semantic drift or a reproducibility mismatch, which would be a determinism problem; others not excluded. The visible data does not choose between them.
- Possible next steps, not started: make the test's assertion print `failure_kind` and `failure_reason` (a test edit in `tests/arena`, not a perf-owned path), then read the next scheduled slow run; or run the slow lane's whole process locally, which is a much larger run.


## Test Summary

## Files Changed

## Completion Summary
