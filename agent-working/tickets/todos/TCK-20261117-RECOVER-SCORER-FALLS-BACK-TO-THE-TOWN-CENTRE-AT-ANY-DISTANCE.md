---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-RECOVER-SCORER-FALLS-BACK-TO-THE-TOWN-CENTRE-AT-ANY-DISTANCE
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-RECOVER-SCORER-FALLS-BACK-TO-THE-TOWN-CENTRE-AT-ANY-DISTANCE

## Title
RecoverScorer falls back to the town centre at any distance

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Deeper issue 8. RecoverScorer's fallback destination is the town centre with no distance bound, so a wounded subject anywhere may be sent across the map. Related: TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT (the sentinel default) and TCK-20261029-HUNGER-SIDE-WAYS-HAVE-NO-DISTANCE-BOUND (the same shape for hunger).

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Count, with no behaviour change, the recover fallbacks by distance on the gate worlds.
2. Designer rules on a bound (or on reading Item 4's known places).

## Out of Scope
- The sentinel-default question (its own ticket).

## Acceptance Criteria
- The counts are reported; if a bound is ruled, a test pins it.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/mechanics/ (the chapter for this subsystem)

## Related Stored Artifacts
- none yet

## Related Code Areas
- as named in the Request Summary

## Assumptions / Open Questions
- The line numbers are on main bb26e4e5f, from the designer's reading; re-check them before acting.

## Implementation Notes
- Phase 3.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
