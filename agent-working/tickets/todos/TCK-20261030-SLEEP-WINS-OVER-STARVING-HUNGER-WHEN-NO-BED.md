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
- 2026-11-03 non-person counterpart filed: TCK-20261103-A-CREATURE-WITH-BOTH-NEEDS-PRESSING-NEITHER-SLEEPS-NOR-FEEDS-ENOUGH. Related base finding: TCK-20261103-BROKE-HUNGRY-WORKERS-STILL-TAKE-NO-SHIFT-ON-MAIN (FATIGUE holds 63% of those workers' starving ticks).
2026-11-03 evidence from the pinned runner (rpg-planner-ubuntu's rows, relayed by rpg-designer and lead-planner-u24; not checked by rpg-planner):
- crowded s42 base (65d43dfa9), e30 leader: FATIGUE 97.85 over HUNGER 63.97 at hunger 59. Caution (rpg-designer): hunger 59 is just past the onset, not "starving hunger". It is evidence about where the two scales cross, which this ticket should state, not proof of its defect.
- crowded s45 base, e34 raider: FATIGUE over HUNGER at hunger 90-99.
- Both bodies also appear on TCK-20261103-TWO-UNOWNED-V3-STARVATIONS-APPEARED-ON-MAIN-WITH-THE-RETREAT-FIX (e30). Their starvation records' last_meal_tick and UNTRIED_STEP are caveated by TCK-20261103-THE-STARVATION-RECORD-MISSES-MEALS-WITHOUT-AN-INTENT-RESULT.
COUNTS (2026-10-30, lane B, 30 runs at EARN 0efd21a61, /mnt/data/scratch-rpg-implementer-2/sleep/out/):
- D73-shape: 509 holds; 42,445 forced ticks (debt >= collapse_line 98) and 19,674 chosen; the hunger wake fired 1,947 times in chosen ticks and sleep was re-chosen every time.
- MAIN (CLAMP): 306 holds (292 bed REST, inn meal open), 38,513 chosen ticks, 3,770 wakes re-choosing sleep; ate later 156 / unfed 142 / died 8.
- A bed and rough rest both recover at -0.1/tick.

DESIGNER RULING (rpg-designer, 2026-10-30):
1. Bible 04 l.38 is a GUARANTEE, so this is a Bug Fix. In the hunger-woken re-decision: if the subject was in a CHOSEN sleep or rest (debt < collapse_line) and a hunger way is open by admits() (ONE-ADMISSION), take the hunger goal; sleep is not re-chosen at that decision. A present threat to life still outranks it. Collapse (debt >= line) is untouched. No score change, no new constant, no owner row unless the paired run STOPs.
2. Reading (i) in the same rule: on a priced meal, a takeable earning step (EARN shift_takeable) counts as an open way. Bible 04 l.38 gains the clause "(on a priced meal, a takeable step that earns it counts as an open way)"; the l.38 diff goes to the designer.
3. Tests:
   (a) main: a starving bed-REST subject with the inn open is woken and goes to EAT;
   (b) a collapse is still forced;
   (c) a threat present means the threat answer wins;
   (d) D73-shape: a chosen rough SLEEP with a takeable shift is woken into WORK.
4. Paired runs on main AND D73-shape. Expected on main: chosen hold ticks about 0, ate-later up. A rise in deaths or collapses, or any STARVATION death after holds, is a STOP to the designer.
5. Divergence: Bug Fix, ids 2.152 / STRAT-292; parity entry next to 2.115.
6. For the D73 owner package (not engineering): for each FORCED hold, the subject's activity in the 200 ticks before it (WORK / MOVE / combat / idle), and why a forced hold spans about 100 ticks (does debt exceed 98, or does the hold count the whole span?). WORK first means calibration: starting purses, the shift's debt cost, SHIFT_TICKS.
REVISED RULING (rpg-designer, 2026-10-30, after lane B's STOP).
Finding: the wake-only rule gave EAT/WORK in 1.4% of 1,145 windows; in 89% FATIGUE re-won at the next ordinary decision; in 11% the subject stalled near the target. 2.115's real defect is that an en-route nav-only update sets no task, so a held REST outlives the wake.
Ruling A' (within the l.38 reading; no owner row unless the paired run STOPs):
1. A typed ProjectState.held_for (HUNGER_WAKE), set when a hunger wake ends a CHOSEN sleep with an open way, and cleared only at:
   (a) the subject eats;
   (b) the way closes;
   (c) a threat is answered;
   (d) debt reaches collapse_line.
   Each end has a typed end-reason. The field is hash-neutral when None and visible in the read model. It is not a lock.
2. While held, FATIGUE does not displace the hunger project and rest_in_place does not fire.
3. The wake ends a chosen sleep even when the hunger project is already current.
4. The Bible 04 l.38 held_for sentence is verbatim from the designer, plus clause (i).
5. STOP if deaths rise, or if collapses rise beyond what the held-window count explains.
The nav-stall share (11%) goes to TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK.

## Test Summary
## Files Changed
## Completion Summary
