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

- STATIC FINDING (rpg-implementer-2, 2026-10-29, both d914bace7 and 58c0821dc): no code ever dispatches a WORK action.
  - grep '"WORK"' src finds only the handlers (action_router.py:57 -> work_shift.work_update; building_services.py:44; pipeline_phases/actions.py:53,216). It finds no emitter.
  - src/engine/building_arrival.py:50-56 dispatches EAT at the inn for a hunger project. The comment there says the work shift is dispatched "only on the removal stack, where a meal costs coin". D73 IS that removal stack, and that dispatch was never written.
  - The opening step (EatScorer -> first_open_step -> _earn_then_buy_step, opening_steps.py:145) moves the subject to the inn. Arrival then gives EAT, which is refused below gold 5, and nothing sends the subject to WORK.
  - So the earn path is declared (work_shift.py: SHIFT_TICKS 200, WAGE_GOLD 6) but not wired at arrival. The evidence job should confirm that no 'work' interaction ever appears.

- LIVE CONFIRMATION (rpg-implementer-2 trace3, 2026-10-29, urban s46; pure, hash equal; /mnt/data/scratch-rpg-implementer-2/d73/trace3/):
  - Hero 22: EatScorer gives NO_AFFORDABLE_WAY. first_open_step gives EARN_THEN_BUY targeting building 20000 at (32,19), which is not the inn; the inn is 20003 at (27,20).
  - Hero 22 stands adjacent at (33,19), path_len 0. Each tick the router dispatches EAT at 20000, and it fails with SOURCE_MISSING.
  - _hold_in_place (action_router.py:74) clears the target, and the hunger goal re-points to 20000. The loop runs from about t800 until death, 1100+ ticks, while hunger rises from 40 to 95.
  - So arrival at an EARN_THEN_BUY target sends EAT, never WORK.
  - Base d914bace7: all 7 s46 workers and hero 22 live to t5000 on free meals at 20003. In D73 all 8 die between t1784 and t2274, every one with last_attacker entity 14, at x28-35 y17-22.
  - First divergence: t587, worker 4's 5 gold, which base takes with no meal (fits N1; not traced).
  - Building 20000's kind is not logged. Check it first.

## Scope
- First, evidence (lane B job, queued after lane A's s46 :1610 trace). Urban s46, on 58c0821dc and on base d914bace7:
  - per decision: the winner's kind and utility against the WORK_SHIFT candidate's utility, or the reason it was not a candidate (no work_in_reach, a leash, a gate, the cap);
  - whether the row-27 earn opening step (a STUB at #454) is wired today, with file and line;
  - hero 22's HOLD: move target, path existence, and why the move is held;
  - base: the first tick where it diverges, and whether the 7 workers eat for free and live.
- FIRST ARTIFACT (rpg-designer, 2026-10-29): a failing real-kernel test for the owed scenario (l.1015): a broke, hungry worker beside the inn, with work there, ends with gold above 0 and a meal eaten. It must fail on both d914bace7 and 58c0821dc today.
- ARITHMETIC before any fix shape: does a 200-tick shift (SHIFT_TICKS) fit before the starvation line? Check that a person's hunger rate (half the base rate, decision 33) x 200, added to hunger at arrival, stays under 95. Check it at the escalation onset (57) and at the observed arrival levels (89-100). If it does not fit, rpg-designer rules (row 27 leaves "how far ahead" to engineering) between:
  - (i) earning taken as a step before the need is pressing (chosen below onset when gold < price);
  - (ii) the shift ends early once the wage covers a meal;
  - (iii) a disclosed gap.
- Lean fix shape, for the evidence to confirm (rpg-designer):
  - On arrival (building_arrival.py about l.50), when a hunger project's EAT cannot be paid and the building's work_in_reach offers a shift, dispatch WORK (work_shift.work_update).
  - The project stays current, and EAT follows on the next arrival or decision once gold >= the price.
  - No new constants: SHIFT_TICKS 200 and WAGE_GOLD 6 already exist.
  - It lands on the D73 stack after PRICED-WAY, because with the free meal ON it never fires.
- ask stays a stub. That is out of scope and already disclosed under row 27.
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
