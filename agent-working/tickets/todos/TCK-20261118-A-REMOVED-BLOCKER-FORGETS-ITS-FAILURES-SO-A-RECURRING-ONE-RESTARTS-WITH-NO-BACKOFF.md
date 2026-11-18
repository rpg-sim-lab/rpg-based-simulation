---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261118-A-REMOVED-BLOCKER-FORGETS-ITS-FAILURES-SO-A-RECURRING-ONE-RESTARTS-WITH-NO-BACKOFF
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-REMOVED-BLOCKER-FORGETS-ITS-FAILURES-SO-A-RECURRING-ONE-RESTARTS-WITH-NO-BACKOFF

## Title
When the quiet-spell rule removes a blocker, its failure_count and backoff go with it, so a blocker that recurs is re-inferred fresh at failure_count 0 and a resolve_blocker project is rebuilt within ticks

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Found by the churn fix's own-job (S9 on #715; tree 18c3250a4; bar B5 tripped in urban_political s42, eid 11; the same shape on s123 eid 22). Lane C traced it from the spy rows, and rpg-designer ruled it on 2026-11-18 as lawful under the ruled design but a design gap.
- Trace, eid 11, blocker_congestion. Build 109 times out at t170 (failure_count 1, backoff 100). Build 269 starts at the end of the suppression. At t297 the quiet-spell rule removes the blocker (last_seen 96 + 200), so project 269 ends COMPLETED BLOCKER_CLEARED. Congestion recurs, and a NEW blocker with failure_count 0 gets a build at t309, 12 ticks after the removal, inside no suppression. Later builds back off as ruled.
- So 5 builds land in 1000 ticks. It is not a never-exit loop (the gaps grow), but it is a bounded re-churn wherever congestion keeps recurring.
- Main vs fix (own-job, report): builds 429 -> 190 (urban s42) and 339 -> 209 (s123); B5 rows 22 -> 1 and 20 -> 1. This ticket covers the residue.

## Scope
1. rpg-designer rules the memory: keep a subject's failure memory per blocker id (or per blocker subject) across removal for a decay period, so a recurring blocker restarts its backoff from where it was. The ruling also sets whether the quiet spell should be judged on last_seen while projects still target the blocker (last_seen 96 while a project was built at 269).
2. A typed record with a defined lifecycle (the Durable State Rule), FIELD_RULES, checkpoint and tests: a removed-then-recurring blocker keeps its backoff; memory past the decay period is forgotten.
3. Own-job: B5 = 0 on the 3 cells, no other churn bar regresses.

## Out of Scope
- The churn fix itself (TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION).

## Acceptance Criteria
- A recurring blocker removed by the quiet spell does not restart at failure_count 0 inside the decay period. A test pins it.
- The own-job shows B5 = 0.

## Related Tickets
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (found by its own-job)
- TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS (blocker inference lives in intelligence.py; land after the split)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (blocker inference, quiet spell, backoff)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/blockerchurn/cells_fix/urban_political_s42_spy.json (the B5 row), summary_fix.txt

## Related Code Areas
- src/systems/strategic_systems/blocker_lifecycle.py (quiet_spell_update, reinferred_blockers_update), intelligence.py (infer_blockers)

## Assumptions / Open Questions
- The decay period length and the memory's key (blocker id vs subject) are rpg-designer's call.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
