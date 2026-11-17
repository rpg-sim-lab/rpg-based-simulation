---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW

## Title
Recruitment's social fatigue counts "recent" rejections, but no window exists, so the counts are lifetime

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Requested by rpg-designer on 2026-11-09, in its ruling on TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME.

src/systems/social_systems/appraisal.py:125 reads `recent_rejections = entity.social.rejection_count.get(contract.source_id, 0)`. Nothing ages or decays rejection_count. Once the wipe bug is fixed, the counts are lifetime, bounded only by the 0.5 penalty cap (5 rejections).

`last_offer_tick` is per subject, not per offerer, so it can't serve as the window as it stands.

## Scope
1. Design (rpg-designer): what "recent" means: a tick window, a decay, or per-offerer last-rejection ticks. Also the constant, and its Bible text (ch07 / social_systems_contract.md).
2. Implement through typed state: a per-offerer tick or decay in SocialComponent, hashed, with the apply-path tests.
3. A paired measurement on the pinned runner, against the bar rpg-designer sets.

## Out of Scope
- The wipe bug and the merge sum (TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME).

## Acceptance Criteria
- rpg-designer's design is recorded in the Bible and the parity ledger.
- The tests cover a rejection aging out, and a count inside the window still counting.
- Hot-loop: maybe. Timing is NOT MEASURED under the perf pause (#715 6556861718).

## Related Tickets
- TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME (must land first)

## Related Docs
- docs/mechanics/ ch07 :65, social_systems_contract.md :59

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/appraisal.py:125
- src/core/models/social.py:58 (rejection_count, last_offer_tick)

## Assumptions / Open Questions
- Needs rpg-designer's design before scoping, and a dispatch decision under the depth rule (#715 6731764470). It's P3, so it's likely deferred.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
