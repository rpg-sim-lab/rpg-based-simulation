---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-INTELLIGENCE-RAW-TIME-PATHS-ARE-UNCALLED
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-INTELLIGENCE-RAW-TIME-PATHS-ARE-UNCALLED

## Title
intelligence.py :912 and :1005-1016 are uncalled paths that read raw world time

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Deeper issue 4. Two paths in intelligence.py (:912, :1005-1016) read raw world time and have no caller. They're dead code that would misread night if revived (see TCK-20261115-THE-NIGHT-CHECK-READS-RAW-WORLD-TIME-SO-EVERY-TICK-AFTER-1800-IS-NIGHT).

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Confirm there are no callers (graphify + grep).
2. Delete them, or route them through the time_of_day helper if a caller is planned.

## Out of Scope
- The night-check fix itself (M1 Item 5's prerequisite).

## Acceptance Criteria
- No uncalled raw-time path remains in intelligence.py; hash-equal on the 3 gate worlds at s42.

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
- Phase 3 (dead code); may ride with Item 5's night helper if it's cheap.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
