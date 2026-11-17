---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-FACTION-TENSION-FROM-REAL-ACTS
phase: open
date: 2026-10-31
tags: []
---

# TCK-20261031-FACTION-TENSION-FROM-REAL-ACTS

## Title
Faction tension comes from real acts between factions (pairwise_tension), measured on current main first

## Status
OPEN (post-v1; counts first; seated by rpg-planner in the 2026-10-31 ticket cleanup, owner go #715 6543261623)

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Split from TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION, closed by disposition: its rarity premise is gone (TCK-20260919 fixed the hostility test; triage: combat is now decisional), but its other finding, pairwise_tension 0.0 in 3 of 4 sampled worlds (measured 2026-09-15, before that fix, so stale), has no ticket. v1_disclosure.md:78 (row S4) names "tension from real acts" as open; the D33 / Q1 `faction_tension_overrides` removal (v1_disclosure.md:49) has no ticket either.

## Scope
Phase 1 (read-only, counts first): pairwise_tension per faction pair across 4 or more worlds on current main (the 3 gate worlds plus one more), at 2000 and 5000 ticks; which acts feed it today (producers, file:line); how much of the value comes from `faction_tension_overrides` content. Report to rpg-planner, which forwards to rpg-designer.
Phase 2: fix shape after rpg-designer reads Phase 1, sequenced after the Q1 override removal.

## Out of Scope
- Cross-faction combat rarity (gone).
- The Q1 override removal itself.

## Acceptance Criteria
(Phase 2, designer to confirm) Faction tension rises from recorded acts between faction members; no constant override is needed for it to be non-zero where the factions interact.

## Related Tickets
- TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION (closed by disposition); TCK-20260919 (hostility test fix)

## Related Docs
- docs/plans/systemic_world/v1_disclosure.md (S4 :78, Q1 :49)

## Related Stored Artifacts
- none

## Related Code Areas
- faction tension producers (to locate in Phase 1)

## Assumptions / Open Questions
- Phase 1 needs a heavy-host slot (rpg-planner allots).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
