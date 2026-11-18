---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-A-DANGER-CONCERN-IS-NEVER-REMOVED-ONCE-ITS-HOSTILE-NO-LONGER-MATTERS
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-A-DANGER-CONCERN-IS-NEVER-REMOVED-ONCE-ITS-HOSTILE-NO-LONGER-MATTERS

## Title
A danger_hostile concern is never removed or refreshed once its hostile no longer matters

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by lane D's Read A (simq_routing_test s42): entity 3's concern danger_hostile_21 (urgency 0.8) was added at t=87 and never removed or refreshed, through a whole harvesting project (t=137-237). Durable state with no defined lifecycle end, against CLAUDE.md's Durable State rule.

SECOND INSTANCE, probable, not yet checked (rpg-planner-ubuntu via the ubuntu lead, 2026-11-18): on main, hero_guild_routing s42 entity 25 stays in danger-while-harvesting for ticks 276-975. Step 2's count must confirm or rule out that this is the same never-removed concern.

Filed by rpg-planner during M1 Phase 1 (owner #715 6936893143: deeper issues found now are filed and fixed in Phase 3 unless they are hard errors). rpg-designer ruled the class.

## Scope
1. Find the concern writers and any decay or removal path.
2. Count, with no behaviour change, how long danger concerns outlive their hostile (out of sight, dead, far).
3. The designer rules the end rule before code.

## Out of Scope
- Any change in Phase 1 unless it is found to be a hard error.

## Acceptance Criteria
- A danger concern has a defined end (decay or removal), with a test.
- The counts are reported.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (sibling: a lifecycle with no end)

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- none yet

## Related Code Areas
- as named in the Request Summary

## Assumptions / Open Questions
- Line numbers are from the M1 Phase 1 branches on 2026-11-17; re-check before acting.

## Implementation Notes
- Binding M1 rule: species reads via species_of(), label reads via occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
