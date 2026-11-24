---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261123-RETIRE-THE-HELD-ROW-ENTRIES-THAT-OWN-ONLY-SKIPPED-ANCHOR-BAND-TESTS
phase: open
date: 2026-11-23
tags: [testing]
---

# TCK-20261123-RETIRE-THE-HELD-ROW-ENTRIES-THAT-OWN-ONLY-SKIPPED-ANCHOR-BAND-TESTS

## Title
The twelve held-row slow known-red entries for test_grade_regression anchor-band tests own tests that never run in the slow job, so they are retired at their 2026-11-29 expiry

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
In the last scheduled slow run (run 45068558150, main 19f6ecac8, artifact slow-junit) all 18 `test_grade_within_anchor_band_long_run` params SKIPPED with "Calibration report not found: data/calibration/<key>/quality_report.json", and the fast `test_grade_within_anchor_band` params (200t/500t) are not in that junit at all (the file excludes them from the slow mark). `data/calibration/` is gitignored and no step in .github/workflows/slow-regression.yml fills it (docstring of tests/simulation_quality/test_grade_regression.py, TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS); only the non-blocking "SimQ grade-anchor drift (informational)" job in test.yml, on push to main, runs make simq-full-audit-full. So the entries in tools/test_architecture/slow_known_reds.yaml for those 12 tests (ticket TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE, expiring 2026-11-29) match tests that never fail there and appear only as stale mappings. Found by rpg-planner (via lead-planner-u24) and confirmed from the junit by testing-planner; lead-planner has no objection (removing entries that own only skipped tests does not loosen a gate).

## Scope
1. On or after 2026-11-29 remove those 12 entries (9 test_grade_within_anchor_band keys and 3 test_grade_within_anchor_band_long_run keys) from slow_known_reds.yaml. Keep the one corpus entry for test_hero_guild_routing_seed42_1000t_cognition_grade_stability: that corpus test does run.
2. Update tests/unit/tools/test_slow_regression_report.py to match: drop test_real_file_owns_each_held_v1_anchor_key_under_the_held_rows_ticket and its HELD_V1_KEYS table, or reduce the test to assert the keys are unowned. This is a changed existing expectation: it needs an owner yes on #715 before the edit.
3. State the junit evidence in the PR notes.

## Out of Scope
- Measuring drift in the slow job: that needs a calibration step in slow-regression.yml, a larger change that is not proposed.
- The SIMQ-V1 held-rows ticket itself (its cause work stays rpg's).
- The test_corpus_diversity entries.

## Acceptance Criteria
1. The slow report lint is clean and the real-file tests pass without the 12 entries.
2. The corpus hero_guild cognition entry and its pin test are unchanged.
3. The owner's yes for the changed test is logged before the push.

## Related Tickets
- TCK-20261024-SIMQ-V1-HELD-ROWS-NEED-A-CAUSE
- TCK-20260903-WORLD-COMPILE-REPORT-BASELINE-STALENESS

## Related Docs
- tests/simulation_quality/test_grade_regression.py (module docstring)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/slow_known_reds.yaml
- tests/unit/tools/test_slow_regression_report.py

## Assumptions / Open Questions
- If the held rows are re-anchored or the calibration step is added before 2026-11-29, this ticket is re-read, not applied.

## Durable state, lifecycle and clocks
Due on or after 2026-11-29 (the entries' expiry).

## Implementation Notes
Pytest on taskset -c 0-3, --basetemp on /data.

## Test Summary
Not run yet.

## Files Changed
None yet.

## Completion Summary
Open.
