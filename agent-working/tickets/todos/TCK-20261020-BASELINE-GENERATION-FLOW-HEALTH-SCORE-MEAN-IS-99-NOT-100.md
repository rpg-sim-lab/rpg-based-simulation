---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100
phase: open
date: 2026-10-20
tags: [observability]
---

# TCK-20261020-BASELINE-GENERATION-FLOW-HEALTH-SCORE-MEAN-IS-99-NOT-100

## Title
test_baseline_generation_and_cli_flow fails on main: one of 5 runs scores health 95, so the mean is 99.0, not 100.0

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tests/integration/observability/test_baseline_generation_flow.py::test_baseline_generation_and_cli_flow` asserts `health_score_dist.mean == 100.0` and gets `DistributionSummary(count=5, min=95.0, max=100.0, mean=99.0)`. It fails serially, so it is not a race. It fails on plain origin/main 522c75491 (Lane B, 2026-10-20), and rpg-planner noted the same 99 vs 100 on 2026-10-18 while the rpg-next PR was being prepared. So it predates #682. The test was last touched in #9 (28bd6e137). One run's health score dropped to 95, probably because of an engine or observability change since then. The test itself is not wrong.

## Scope
- Find which run scores 95 and which health-score component costs it the 5 points.
- Bisect to the commit that first produced it.
- Decide whether this is a real defect (fix it) or an intended behaviour change. If intended, update the expectation with a written reason and the designer's OK, never just to make the test pass.
- Find out why CI integration did not catch it (marker, selection, or known-reds entry).

## Out of Scope
- Changing the health-score formula without a ruling.

## Acceptance Criteria
- The cause is named with the commit. The test passes for that reason, or its expectation changes with a cited ruling.
- The CI-selection question is answered.

## Related Tickets
- TCK-20260520-SIM-OBS-PHASE4-M17 (origin of the test)

## Related Docs
- docs/archive/sim-obs-test/obs_sim_phase4.md

## Related Stored Artifacts
- none

## Related Code Areas
- tests/integration/observability/test_baseline_generation_flow.py
- src/observability (health score)

## Assumptions / Open Questions
- Is it the same 95 on every seed set, or seed-dependent?

## Implementation Notes
Not a v1 blocker (not on the gate path). It predates v1.

## Test Summary

## Files Changed

## Completion Summary
