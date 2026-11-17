---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261117-NEAREST-SERVICE-IS-PASSED-A-REGION-ID-AS-ITS-SUBJECT
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-NEAREST-SERVICE-IS-PASSED-A-REGION-ID-AS-ITS-SUBJECT

## Title
TownNavigation.get_nearest_service is passed a region id as its subject, so near_service probably never matches

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Deeper issue 2. resources.py:79 passes a region id where get_nearest_service expects the subject, so near_service probably never matches.

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Confirm read-only with a unit probe: what near_service returns on today's main.
2. Count, without a behaviour change, how often the call site runs and whether it ever matches.
3. Propose a fix scoped to the argument; the designer rules before code.

## Out of Scope
- Service selection in general.

## Acceptance Criteria
- The probe result is reported.
- If it's confirmed: a regression test that near_service matches for a subject beside its service, plus a divergence entry if behaviour changes.

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
- Phase 3, unless the probe shows a hard error.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
