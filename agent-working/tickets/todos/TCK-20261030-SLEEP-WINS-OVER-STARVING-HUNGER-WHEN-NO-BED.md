---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED
phase: open
date: 2026-10-30
tags: []
---

# TCK-20261030-SLEEP-WINS-OVER-STARVING-HUNGER-WHEN-NO-BED

## Title
A starving subject (hunger >= 95) holds SLEEP for hundreds of ticks beside a takeable earn step, because the hunger wake's "a way is open" does not count a takeable opening step

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by lane B during EARN (TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO), in the D73-shape probe (ATOMIC + no free relief). Urban s46 person 1, ticks 1900-2150:
- hunger 95 -> 100; sleep debt 95 -> 98 (the collapse line) -> 80.5;
- SleepScorer 185-188 vs EatScorer 155-160 (earn_then_buy -> hiring inn 20003, takeable, no threat): sleep wins every sample by 25-30;
- admits(REST) is false at gold 2, so the subject rests in place (sleep_target None) and holds SLEEP from t1975, 2-3 tiles from the work;
- debt falls 0.1/tick, so the hold lasts about 450 more ticks at hunger 100, with HP recovering 86 -> 92;
- the hunger wake fires, and the re-decision picks sleep again.
On main (CLAMP, base b9287a3de) the same person never gets there: it is fed free (hunger 20 -> 60), and its sleep debt is 60-83. An inn bed also recovers at 0.1/tick.
Raw data: /mnt/data/scratch-rpg-implementer-2/probe/diag2_u46.json, diag2_u44.json, diag_u44.json, diag_u46.json.

Designer framing (rpg-designer, 2026-10-30):
- No ruling covers this. Row 83 orders starvation past its line against present THREATS, not against sleep debt at its line, and both needs are Tier 2.
- Bible 04 l.38 says a woken sleeper "eats if a way is open". Under the earn path no way is open; only a takeable step is. The text never decided whether a takeable opening step counts.

## Scope
1. COUNTS FIRST, with no behaviour change. D73-shape (ATOMIC + no free relief, on top of EARN), 3 worlds × s42-46 × 5000t:
   - how often a subject at hunger >= 95 holds SLEEP or REST while a takeable earn step exists, and the run lengths;
   - its HP and sleep-debt trajectory over that time;
   - outcomes: eats later / starves / alive and unfed at 5000;
   - the same split for a bed vs rough rest; confirm whether both recover at 0.1/tick.
   - Also the main-law counts (CLAMP) for the same measure; expected about 0.
   Send to rpg-planner, who passes them to rpg-designer.
2. The designer rules between two candidates:
   (i) Bible 04 l.38's "a way is open" includes a takeable opening step, so the hunger wake ends a CHOSEN sleep when debt is below the collapse line. Collapse keeps forcing sleep at the line. This is a reading of existing text, so it is the designer's call. The designer leans this way.
   (ii) A scoring change between the two pulls past both lines. That changes need ordering, so it becomes an owner memo row via lead-planner-u24.
3. Implement the ruling. Divergence entry, Bible/parity, paired run on main (expected identical under CLAMP if (i)), and a D73-shape probe.

## Out of Scope
- The payment law (ATOMIC/CLAMP) and starting purses (an owner content/calibration row).
- The stalemate-breaker defect (TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK).
- Whether a bed should recover faster than rough rest, unless the counts show it matters (raise it as a question; don't change it here).

## Acceptance Criteria
- The counts table is delivered and the designer's ruling is recorded in this ticket before any code.
- A test for the s46 p1 shape: hunger >= 95, a takeable earn step, sleep debt below the collapse line, a chosen sleep. The subject is woken and takes the step (if (i) is ruled).
- A test: at the collapse line, the subject keeps sleeping (collapse is unchanged).
- The paired run on main is reported; the D73-shape probe shows the hunger-100 SLEEP holds near a takeable step fall.

## Related Tickets
- TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO (EARN; the source)
- #781 D73 (this ticket is a PRECONDITION of the D73 re-measure)
- TCK-20261011-HUNGER-WAKES-A-SLEEPER (2.115)

## Related Docs
- docs/mechanics/04_strategic_cognition.md (l.38, Standing Needs Escalate, hunger wakes a sleeper)
- docs/world_rules/life-body/survival-needs.md (SURV-07, SURV-02 amendment / decision 41)
- docs/guidelines/intentional_divergences.md 2.115

## Related Stored Artifacts
- /mnt/data/scratch-rpg-implementer-2/probe/ (diag*, F/, E/)

## Related Code Areas
- src/ai/goals/scorers.py (SleepScorer, EatScorer), src/engine/need_wake.py, the scheduler's hunger wake, src/engine/starvation.py, src/engine/sleep_debt.py

## Assumptions / Open Questions
- Sequence: after EARN merges; before the #781 re-measure.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
