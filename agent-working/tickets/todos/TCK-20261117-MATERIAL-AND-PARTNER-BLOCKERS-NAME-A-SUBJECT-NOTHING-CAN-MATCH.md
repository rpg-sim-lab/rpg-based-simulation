---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-MATERIAL-AND-PARTNER-BLOCKERS-NAME-A-SUBJECT-NOTHING-CAN-MATCH
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-MATERIAL-AND-PARTNER-BLOCKERS-NAME-A-SUBJECT-NOTHING-CAN-MATCH

## Title
Material blockers (subject "resource") and social blockers (subject "suitable_partner") can never resolve, because no item or partner matches those subject strings

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by rpg-implementer-3's churn trace (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION).
- blocker_node_<id> has subject "resource", and resolve_blockers (intelligence.py:711-830) asks has_item(inventory, "resource", 1). No item is named "resource", so it can never resolve.
- block_no_partner_<eid>_<tick> has subject "suitable_partner", the same pattern.
- In urban_political s42 1000t they account for 21 + 5 of 93 resolve_blocker projects.
rpg-designer ruled these OUT of the churn fix: with its merge, typed timeout and backoff they're bounded, so they're no longer a liveness failure. But a blocker whose subject can't match anything is a real bug. It's a Phase 1 ticket that does NOT gate run 1.

## Scope
1. For each writer: decide, through the designer, whether to fix the subject key (the real item id, or a partner predicate) or remove the writer.
2. Add a test that every blocker kind a writer can produce has a reachable resolution path.

## Out of Scope
- The congestion blocker (handled in the churn fix).

## Acceptance Criteria
- No blocker writer produces a subject its resolver can never satisfy (a static or unit test).

## Related Tickets
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION
- TCK-20261101-A-NO-PARTNER-BLOCKER-IS-RE-CREATED-EVERY-TICK

## Related Docs
- docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data2/rpg-measure/n10/capread/rb_evidence_n10_s42.txt

## Related Code Areas
- src/systems/strategic_systems/intelligence.py (infer_blockers, resolve_blockers)

## Assumptions / Open Questions
- Line numbers are from 67b507f8c.

## Implementation Notes
- MOVED OUT of systemic_foundation (M1) to the cognition-rework backlog, 2026-11-25. Owner ruling #715 7157496515 Q2 (only HARD K1-K5 repairs stay); rpg-designer's classification posted as #715 7157686023 and recorded by the lead as 7157730160. Reason: bounded since the churn fix (typed timeout plus back-off); a real bug, but not liveness.
- Filed by rpg-planner on rpg-designer's ruling (2026-11-17).

## Test Summary

## Files Changed

## Completion Summary
