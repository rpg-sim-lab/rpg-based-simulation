---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261117-WEATHER-PERCEPTION-MULTIPLIER-HAS-NO-READER
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-WEATHER-PERCEPTION-MULTIPLIER-HAS-NO-READER

## Title
Weather's perception multiplier is written but never read

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Deeper issue 5. Weather computes a perception multiplier that no perception code reads.

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Confirm read-only.
2. Designer rules: wire it into M1 Item 3's honest perception, or delete it.

## Out of Scope
- New weather behaviour.

## Acceptance Criteria
- Either a reader with a test, or the field removed; no write-only field remains.

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
- Phase 3, or folded into Item 3 if the designer says so.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
