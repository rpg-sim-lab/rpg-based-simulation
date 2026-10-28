---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO
phase: open
date: 2026-10-29
tags: []
---

# TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO

## Title
A subject that starts broke never takes paid work when hungry, so it earns no wage in 5000 ticks, and removing the free meal (D73) starves it

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
D73 (#781) traces, urban_political, tree 58c0821dc (src = 7cfd2cc0c). Files: /mnt/data/scratch-rpg-implementer-2/d73/trace2/{u46,u42}.jsonl.
- s46 hero 22: gold 0 for all 5000 ticks. Never ate. Stood in HOLD at [33,19] from about t1700. Died t1916, STARVATION after a hit.
- s42 scout 17: started with gold 5, which is exactly one meal. Ate once at t2053, then gold 0 for 2000+ ticks. Died t4078, STARVATION after a hit.
- s46 workers 4, 8, 3, 2, 5, 1 and 7: all broke, hunger 89-100. All died in DEFEAT, in one cluster at about x28-35 y17-22.
- No subject earned any wage. WORK_SHIFT was in reach and never taken.

rpg-designer ruling (2026-10-29). Sources: survival-needs.md l.925-936 and the owed scenarios l.1010-1017.
- The free-meal removal was parked by the owner's earlier ruling "until earning works".
- D73 does NOT land until broke-and-hungry -> earn is shown to work. Landing it with a disclosure instead would reverse the owner's ruling, and that needs an owner question through lead-planner-u24.

## Scope
- First, evidence (lane B job, queued after lane A's s46 :1610 trace). Urban s46, on 58c0821dc and on base d914bace7:
  - per decision: the winner's kind and utility against the WORK_SHIFT candidate's utility, or the reason it was not a candidate (no work_in_reach, a leash, a gate, the cap);
  - whether the row-27 earn opening step (a STUB at #454) is wired today, with file and line;
  - hero 22's HOLD: move target, path existence, and why the move is held;
  - base: the first tick where it diverges, and whether the 7 workers eat for free and live.
- Then the fix shape goes to rpg-designer. Not before.
- Fix, measured as its own step: paired 3 x s42-46 x 5000t (decision 76).

## Out of Scope
- Price-aware "open": TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY.
- The bed scorer gold gate: TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR. Sequenced next to this ticket.
- Wage sources and amounts (decisions 34, 37, divergences 2.102, 2.117).

## Acceptance Criteria
- The owed scenario at survival-needs.md l.1015, shown live on the urban s46/s42 subjects: "a hungry worker with no gold beside the inn is not fed, goes to its paid work, and eats once it can pay."
- A real-kernel test of the same.
- A paired run with no unowned STOP. The divergence entry and Bible/parity updates as the fix requires.
- Once this lands, D73 can be re-measured.

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (D73, #781, blocked on this ticket)
- TCK-20261029-A-PRICED-WAY-IS-OPEN-ONLY-TO-A-SUBJECT-THAT-CAN-PAY
- TCK-20261028-BROKE-SUBJECT-WALKS-TO-THE-INN-BED-IT-CANNOT-PAY-FOR
- TCK-20261007-A-NEED-WITH-NO-OPEN-WAY-PULLS-TOWARD-THE-STEP-THAT-OPENS-ONE-SURV-07-AMENDMENT
- TCK-20261009-WAGE-IS-PAID-FROM-THE-EMPLOYERS-OWN-PURSE-EXCH-02, TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN

## Related Docs
- docs/world_rules/life-body/survival-needs.md (SURV-06, SURV-07 row 27, parked note l.925-936, owed scenarios l.1010-1017)
- docs/world_rules/scenarios/material-economy-batch-08.md (ME-S20, ME-S21)
- docs/guidelines/intentional_divergences.md 2.102, 2.117, 2.142

## Related Stored Artifacts

## Related Code Areas
- src/ai/goals/ways.py (work_in_reach, first_open_step), src/ai/goals/scorers.py (EatScorer opening_step, work scorer)

## Assumptions / Open Questions
- Is the earn opening step still a stub? The evidence job answers this. If it is, this ticket is the real D73 blocker. Not dispatched.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
