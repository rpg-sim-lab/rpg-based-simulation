---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-LEAD-CREATE-AND-RESOURCE-SITE-RECORD-HAVE-NO-CALLER
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-LEAD-CREATE-AND-RESOURCE-SITE-RECORD-HAVE-NO-CALLER

## Title
LeadService.create_lead and SpatialMemory.record_resource_site have no caller

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Deeper issue 7. Two knowledge-writing entry points have no caller: LeadService.create_lead and SpatialMemory.record_resource_site. M1 Item 4 (places from perception and memory) may be their natural caller.

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Confirm there are no callers.
2. Designer rules: Item 4 calls them, or they go.

## Out of Scope
- Item 4's own design.

## Acceptance Criteria
- Each method has a live caller with a test, or it's removed.

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
- Phase 3, or folded into Item 4.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
