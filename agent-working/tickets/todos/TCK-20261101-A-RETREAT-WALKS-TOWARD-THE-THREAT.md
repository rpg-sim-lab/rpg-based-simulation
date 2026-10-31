---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261101-A-RETREAT-WALKS-TOWARD-THE-THREAT
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-RETREAT-WALKS-TOWARD-THE-THREAT

## Title
A retreat walks to the town centre even when that path closes on a present threat

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Designer ruling 2026-11-01, from the retention STOP #2 (TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT, lane C, fix afacf1577, crowded s46). A COMBAT_RETREAT's destination is town_center wherever the threat is. In crowded s46, e14 walked a steady diagonal (66,94) -> (33,32) toward the town centre at hp 6-10/85, met three hostiles at t463, and died at t542 still holding the retreat. Six of the nine fix-only dead in that run held a retreat adopted 1-30 ticks before death. Whether the walk brought them closer to their killer than standing would have is NOT measured: out10 has no positions. COUNTS FIRST, on the retention (d)-alone batch.

## Scope
Read-only counts on the (d)-alone re-measure batch (same 15 runs, 2000t, base 6fdfdf555), from the same runs:
1. For every COMBAT_RETREAT: the distance to the nearest present hostile at adoption, its minimum over the walk, and at the end. The share where the minimum is below the distance at adoption (the walk closed on a threat).
2. For every death while holding a retreat: the killer id; whether it was the threat present at adoption or one met en route; the distance trend to the killer over the last 30 ticks.
3. For each, the base arm's position and fate for the same subject.

## Out of Scope
Any fix (the designer rules the shape from the counts). The retention completion rule. The project-cap exemption (an open row in law P's grid, TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED, which also needs these counts).

## Acceptance Criteria
- AC1-AC3: the three tables, base stated, probe hash-neutral.
- AC4: the designer's ruling recorded here before any plan.

## Related Tickets
TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT; TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED; TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK.

## Related Docs
docs/mechanics/04_strategic_cognition.md (AGENCY-07, present_threat_to); docs/guidelines/intentional_divergences.md 2.156.

## Related Stored Artifacts
The retreat worktree: staging_artifacts/TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT/evidence/full_batch_afacf1577/analysis_full10.md.

## Related Code Areas
src/ai/goals (CombatRetreatScorer target), src/engine/tactical.py, src/engine/pipeline_phases/movement.py.

## Assumptions / Open Questions
The designer's lean (not a ruling): flight is "away from the threat"; the step choice must not reduce the distance to any present threat, with town_center kept only while its path complies; a threat-relative destination is the alternative. If the (d)-alone batch shows no per-world death rise, this is P3; if it rises and the victims were walking retreats, it becomes the next blocker before retention lands. The counts ride on lane C's (d)-alone batch.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
