---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT

## Title
A retreat project outlives its threat (entity parked on COMBAT_RETREAT ~950 ticks with no threat, recovered, not moving)

## Status
OPEN (counts-first; trace on the ubuntu side per rpg-designer 2026-10-31; seated by rpg-planner)

## Tier
standard (provisional; the designer sets the fix shape after the counts)

## Type
bug

## Priority
P1 (blocks the #769 SimQ re-anchor of urban_political s42)

## Request Summary
Found by rpg-designer's #769 check (TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT, evidence/designer_check/README.md at f0e5a2897 on rpg-ubuntu-simq-anchor-bisect-impl). At d914bace7, urban_political s42 2000t, entity 18 holds proj_combat_retreat_42 over t63-1402: 950 ticks after t452 with no perceived hostile, 742 of them at hp >= 0.5, ~200 at full hp, sitting at about (25,25); retreat_pull changes no score and COMBAT_RETREAT is never the top raw score. Replaced by proj_fatigue_1402 at t1403. Pre-existing retention: #769's src diff is only the scorer and retreat_pull, it only changes who reaches it. #769 itself is CLEARED (designer ruling 2026-10-31).

Designer reading: a retreat moves away from perceived threats (tactical contract section 4, GAP-T03). Recovering while hurt is fine but is RECOVER/REST or no project, never COMBAT_RETREAT; idling at full hp is wrong under any label. A retreat project should end when its threat is gone AND the entity is clear of it; recovery is then an ordinary re-decision. Death should close open projects (count only here).

## Scope
Phase 1 (counts first, read-only probe, ubuntu side). Answers to the designer:
1. Which path keeps proj_combat_retreat_42 each tick t63-1402: (i) a pending COMBAT_RETREAT committed intention re-injected at _COMMITTED_INTENTION_BASE_UTILITY (intelligence.py ~1546; COMBAT_RETREAT is in _COMMITTED_INTENTION_ELIGIBLE_KINDS, :107-111), (ii) the best_candidate filter (intelligence.py ~1586: utility < 20 or no target_id/target_pos skipped; None keeps the current project), or another.
2. What ends it at t1403, and through which path.
3. Width: across 3 worlds x s42-46 at a25619971 and d914bace7, count retreat projects still active N ticks after their last present threat (N = 50, 200, 1000) and distinct entities; is "no living retreat holder" at the parent true across all seeds.
4. Dead entities with an open project (any kind).
Phase 2: fix shape from the designer after reading 1-4.

## Out of Scope
- #769 (cleared). The groups-id fix (TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP), sequenced together with this before the s42 re-anchor.
- Closing projects on death (counted only).

## Acceptance Criteria
(Phase 2, designer to confirm) No retreat project active after its threat is gone and the entity is clear; recovery shows as RECOVER/REST or no project; width counts at N=50 fall to about 0; no death/combat regression; s42 re-measured before the re-anchor.

## Related Tickets
- TCK-20261030-SIMQ-ANCHOR-REDS-SINCE-V1-REANCHOR-NEED-A-BISECT; TCK-20261031-A-NEW-GROUP-ID-OVERWRITES-A-LIVE-GROUP; TCK-20260812-COMMITTED-INTENTION-SEQUENCE; TCK-20261002-COMBAT-OBJECTIVE-TARGETS-ENTITY-VIA-FIXED-POINT-AND-NEVER-TERMINATES (precedent: end a combat objective when its reason is gone)

## Related Docs
- docs/engine/contracts/tactical_contract.md section 4 (GAP-T03); docs/mechanics/04_strategic_cognition.md (goal hierarchy, interruption resistance)

## Related Stored Artifacts
- rpg-ubuntu-simq-anchor-bisect-impl f0e5a2897: evidence/designer_check/README.md

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (committed intentions, best_candidate ~1586), src/ai/goals/scorers.py (retreat scorer ~230-239)

## Assumptions / Open Questions
- Whether other committed-intention kinds (ENGAGE, RESOLVE_BLOCKER) can be held the same way.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
