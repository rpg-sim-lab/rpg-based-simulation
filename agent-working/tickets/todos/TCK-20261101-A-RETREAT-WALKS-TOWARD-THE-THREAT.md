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
P3

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

## 2026-11-01 priority and named case (rpg-designer ruling on the retention re-measure)
- Priority is now P3. No Tier 1, and walks toward the threat are about a third on both arms (fix 5c6001620 vs base: 15/37 -> 11/32; trend closing 12 -> 8). Not worse with the retention fix.
- Named case: e9 (frontier s46, 2000t), byte-identical on base 6fdfdf555 and the retention fix 5c6001620 (hash 45002e515a), so it's a base gap. CORRECTED 2026-11-01 by lane C: e9 does NOT die in this set. The t1056 death was the earlier cap-exempt batch.
  - It holds retreat_431 for 1176 ticks in six segments: 432-641, 692-1085, 1092-1123, 1132-1171, 1192-1611 and 1632-1711.
  - It is alive at t1999 with hp down to 0.05.
  - Retreat walk ends by segment: (33,28)->(12,22), (10,14)->(19,29), (17,30)->(11,18), (20,18)->(25,25), (21,31)->(15,35), (32,31)->(34,10).
  - Nearest hostile, first/min/last per segment: 3/1/11, 3/1/1, 4/1/1, 2/1/3, 5/1/1, 8/1/1. So it is at distance 1 in every segment.
  - present_threat_to was true on 108/210, 215/394, 32/32, 24/40, 419/420 and 80/80 ticks.
  - The retreat repeatedly walks through hostile-adjacent tiles. No town_center end is logged.
  - **Counts-step addition for e9 (rpg-designer, 2026-11-01):** a hostile at distance 1 in every segment for 1176 ticks, with e9 alive at hp 0.05, may be a STALEMATE rather than a walk toward the threat. For each segment, record:
    - attacks by the adjacent hostile on e9;
    - tiles e9 moved, and why it doesn't reach town_center (blocked path, congestion or re-targeting);
    - the hostile's own goal.
    If e9 barely moves and the hostile barely attacks, link the case to the STALEMATE/WANDER nav family (TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK). No 5000t base run (designer).
