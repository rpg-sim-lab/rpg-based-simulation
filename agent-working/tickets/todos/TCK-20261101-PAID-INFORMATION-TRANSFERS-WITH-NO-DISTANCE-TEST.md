---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST

## Title
Paid information transfers a lead and gold between two entities with no distance test (counts first)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Ubuntu's lodger path list (row 22, lodger_decision_paths_2026-11-01.md at c721b3316) found that paid_information.py:98 transfers a lead and gold with NO distance test, for any pair of entities, lodged or not. rpg-designer ruled on 2026-11-01 that the non-lodging half is a pre-existing defect apart from lodging. It gets its own counts-first ticket. The lodged half stays in TCK-20261101-A-LODGER-DECISION-PATH-AUDIT. Not yet verified against the code.

## Scope
Counts first, no fix shape before the counts and a designer ruling:
1. Verify paid_information.py:98 and its caller at the current main head. Is there any distance, region or co-location check upstream?
2. On existing or hash-neutral probe runs (batch C seeds), per run: paid-information transfers; the buyer-seller distance distribution; the share beyond interaction range (state the range used); and gold moved.
3. Name the writer and the Bible / parity entry that governs information trade (ch.03 economic laws or ch.04 knowledge).

## Out of Scope
- The lodged half (the audit ticket).
- Any fix before the counts and the ruling.

## Acceptance Criteria
- The counts 1-3 are reported, and rpg-designer rules: a distance or co-location rule shape, or by design (with a Bible citation).

## Related Tickets
- TCK-20261101-A-LODGER-DECISION-PATH-AUDIT
- TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS

## Related Docs
- docs/mechanics/03_economic_laws.md; docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- lodger_decision_paths_2026-11-01.md at origin rpg-ubuntu-planner-idle, c721b3316198b4158316194f61fc0deb2acd2141 (row 22)

## Related Code Areas
- src/engine/pipeline_phases/paid_information.py:98

## Assumptions / Open Questions
- Hot-loop: unknown until the investigation.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
