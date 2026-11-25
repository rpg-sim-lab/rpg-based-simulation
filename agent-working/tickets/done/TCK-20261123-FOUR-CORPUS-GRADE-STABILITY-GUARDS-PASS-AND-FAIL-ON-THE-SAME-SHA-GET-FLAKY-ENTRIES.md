---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261123-FOUR-CORPUS-GRADE-STABILITY-GUARDS-PASS-AND-FAIL-ON-THE-SAME-SHA-GET-FLAKY-ENTRIES
phase: done
date: 2026-11-23
tags: [testing]
---

# TCK-20261123-FOUR-CORPUS-GRADE-STABILITY-GUARDS-PASS-AND-FAIL-ON-THE-SAME-SHA-GET-FLAKY-ENTRIES

## Title
Four corpus grade-stability guards that pass and fail on the same sha in the scheduled slow run are owned as flaky known reds, and the re-anchor pin test accepts only a flaky owner

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
"Slow regression" runs 45068558150 (main 19f6ecac8) and 45011543158 (cae7f4078) fail four test_corpus_diversity grade-stability guards that no entry in tools/test_architecture/slow_known_reds.yaml owns. The same four failed at 613a8365b on 2026-11-21 20:39 and PASSED at the same sha on 2026-11-22 00:40; c540a0b17 (fail 11-20 10:27, pass 11-20 21:56) and 0c18f6151 show the same shape. So this is host or load sensitivity, not a regression. Owner rulings on #715: 7090950152 ("Own as flaky, no rerun") and 7090968271 ("Own all 4, amend the test", option c). The cause is the owner-parked wall-clock throttle ticket TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (BLOCKED until the engine re-architecture).

## Scope
1. Add four `kind: flaky` entries to tools/test_architecture/slow_known_reds.yaml, owner testing-planner, ticket TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2, added_on 2026-11-23, expires_on 2026-12-15, one per test id, each note stating the same-sha fail/pass evidence (613a8365b, c540a0b17, 0c18f6151) and citing #715 7090950152:
   - test_urban_political_seed123_1000t_social_economy_grade_stability
   - test_generated_frontier_3_42_seed123_200t_combat_narrative_grade_stability
   - test_frontier_extended_seed42_200t_narrative_grade_stability
   - test_frontier_extended_seed123_200t_combat_progression_narrative_grade_stability
   (all under tests.unit.worldassembly.test_corpus_diversity::)
2. Amend tests/unit/tools/test_slow_regression_report.py::test_real_file_has_no_owner_for_a_corpus_anchor_after_the_baseline_v1_reanchor: keep every anchor in its parameter list (frontier_extended_seed42_200t_narrative included); the test still fails on any owner that is not kind: flaky and accepts a flaky owner. State the reason in the test: owner ruling #715 7090968271.

## Out of Scope
- Any other entry, the selfmodel_probe entry (already owned as broken), or the workflow.
- A measurement or rerun of the cause (owner: no rerun, no GO).

## Acceptance Criteria
1. The four tests resolve to a flaky entry via srr.owner_of; the real-file lint is clean.
2. The amended test passes, and fails if any of the five anchors gets a broken-kind owner (shown by a one-off check, not committed).
3. Any other test of the file is unchanged. The owner's yes on the push is logged on #715.

## Related Tickets
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (the parked cause)
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (retired the family entries; the pin test's origin)

## Related Docs
- tools/test_architecture/known_reds.py (schema and lint)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/slow_known_reds.yaml
- tests/unit/tools/test_slow_regression_report.py

## Assumptions / Open Questions
- The entries expire 2026-12-15; at expiry the owner re-dates or the cause ticket retires them.

## Durable state, lifecycle and clocks
Entries expire on 2026-12-15.

## Implementation Notes
Pytest on taskset -c 0-3, --basetemp on /data, no uv sync. Changed existing test: owner-approved (#715 7090968271). No bare git stash.

## Test Summary
tests/unit/tools/test_slow_regression_report.py and test_known_reds.py: 128 passed (taskset -c 0-3). The four tests resolve to a flaky entry under the throttle ticket (new parametrized test); the real-file lint is clean. One-off check, not committed: with every flaky entry flipped to broken, the amended pin test fails for frontier_extended_seed42_200t_narrative, the only one of the five pinned anchors that now has an owner; the other four anchors still have none, and the pin still fails for any owner that is not flaky. No rerun, no heavy run.

## Files Changed
tools/test_architecture/slow_known_reds.yaml (4 flaky entries), tests/unit/tools/test_slow_regression_report.py (pin amended, one ownership test added), this ticket.

## Completion Summary
The four guards are owned as flaky until 2026-12-15 under the parked throttle ticket; the re-anchor pin accepts only a flaky owner (owner ruling #715 7090968271). Push yes still to be logged on #715.
