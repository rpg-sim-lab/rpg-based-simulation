---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261101-A-LODGER-DECISION-PATH-AUDIT
phase: open
date: 2026-11-01
tags: []
---

# TCK-20261101-A-LODGER-DECISION-PATH-AUDIT

## Title
Lodger decision-path audit: classify every remaining path a lodged stayer can still take a decision on, counts first (F3 seam 2.155, ticket 2 of 2)

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Ubuntu's path list (59 rows with file:line, lodger_decision_paths_2026-11-01.md at c721b3316 on rpg-planner-ubuntu's seat branch) shows that F3's two entries strip only walk targets. A lodged stayer can still take:
- project and goal records (rows 1-2, intelligence.py:618);
- an information-need project on a hunger wake (row 3, cognition.py:74-78);
- paid information (row 22, lodged half);
- reproduction;
- an engagement posture (row 43 as actor);
- progression conversion (row 48);
- guild visits;
- the not-determined rows (quests, interactions, harvest, blacksmith, rumour, old redirection).
Only 8 rows and the wake rule were checked against the code.

rpg-designer accepted the two-ticket split on 2026-11-01. The social paths are ticket 1 (TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS), which introduces the shared predicate `is_lodged_stayer` and the architecture test. This audit covers every remaining row. The RULE does not split: "a lodged stayer takes no new decision of any kind", with exceptions (a)-(d) only, as written in ticket 1's Rule section. The audit classifies against those exceptions and does not re-open them.

## Scope
For every row of the 59 not covered by ticket 1:
1. (a) Verify the file:line against the code at the audit head.
2. (b) Count how often it fires while lodged. Use the urban s42 and frontier probes from groups batch C, or this ticket's own hash-neutral probe runs.
3. (c) Classify it against exceptions (a)-(d): suppress, or allowed under (a), (b), (c) or (d). The designer's per-row lean:
   - suppress rows 1-2, 3, 6-7, 9, 16, 19, 20, 22 (lodged half), 35, 43, 51;
   - allow row 48 under (b);
   - not-determined rows: expected suppress unless one of (a)-(c) applies.
4. Only a row that fits no exception AND where the ruling looks wrong in practice goes back to rpg-designer as a question, with its counts.
5. Then the fix: the rows classified "suppress" read ticket 1's `is_lodged_stayer` predicate. Their phases are added to ticket 1's architecture-test list. No second mechanism.

## Out of Scope
- The social paths (ticket 1).
- paid_information.py:98's no-distance transfer for non-lodged entities (TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST).
- Re-opening exceptions (a)-(d).
- Lodger-to-lodger interaction in the same building. That owner question waits until after this ticket.

## Acceptance Criteria
- investigation.md holds a table of every remaining row: file:line verified (yes/no and the corrected line), lodged firing count, classification, and the exception cited.
- Every "suppress" row reads the predicate, and its phase is on the architecture-test list. The test passes.
- On a re-measure over the batch C seeds: 0 new decision records by lodged stayers on every listed phase.
- Tests pin the wake outcomes (stay / leave / in-building service only) and that progression is unchanged in or out.
- A run with no lodgers is hash-identical to base. Deaths are paired under the death-STOP bar.
- Bible ch.04, the parity ledger (2.155) and intentional_divergences stay consistent.
- Hot-loop: to be stated per phase by the investigation. Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Related Tickets
- TCK-20261101-A-LODGER-OFFERS-AND-ACCEPTS-RECRUIT-CONTRACTS (ticket 1; predicate, architecture test, rule text). Depends on it landing first.
- TCK-20261031-A-SLEEPER-HOLDS-A-DOOR-OR-SERVICE-TILE (F3; class (a))
- TCK-20261101-PAID-INFORMATION-TRANSFERS-WITH-NO-DISTANCE-TEST
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (groups batch C, the source of the probes)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (section 1); docs/parity_ledger/strategic_cognition.yaml (2.155)

## Related Stored Artifacts
- lodger_decision_paths_2026-11-01.md at origin rpg-ubuntu-planner-idle, c721b3316198b4158316194f61fc0deb2acd2141.

## Related Code Areas
- src/systems/strategic_systems/intelligence.py:618; cognition.py:74-78; paid_information.py:98; appraisal.py:48/:183; and the rest per the path list.

## Assumptions / Open Questions
- Sequenced after ticket 1, because it extends ticket 1's predicate and test list.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
