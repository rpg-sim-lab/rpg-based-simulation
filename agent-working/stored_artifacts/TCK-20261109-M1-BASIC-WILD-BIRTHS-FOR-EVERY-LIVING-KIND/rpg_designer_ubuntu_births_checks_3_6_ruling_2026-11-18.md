---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Births own-job (#715): checks (3) and (6) ruled before data (rpg-designer-ubuntu, 2026-11-18)
- **Basis:** the owner's two checks, relayed by lead-planner. No own-job data exists yet, so this is fixed before data.
- **Comparison arm:** the chance-0 control throughout. It matched main byte for byte (af1807fe858da5eb, 1861807b558c5425), and it is the same build as head.

## (3) Combat deaths: BALANCE, no bar
- **Why no bar:**
  - more bodies give more encounters, so a rise is an expected consequence of births, not a defect;
  - no band was agreed before data, and I won't invent one now;
  - the owner judges outcomes by variety within bands across seeds, not by a target count;
  - a kill-driven collapse is already caught by the extinction line (no exemption, B3).
- **Report format, fixed now:**
  1. Per world × cause × seed, both arms: the raw death count, and deaths per 1000 live entity-ticks, so the rise can be read against the population rise.
  2. A killer kind → victim kind table per world, both arms. Newborns (born in the run) are a separate victim row.
  3. **Consistency, computed mechanically:** per world, the head/control ratio of the per-capita rate in every seed. "Holds" = the ratio is above 1 in every seed. "Mixed" = any seed at or below 1, which reads as chaotic divergence. Print the ratio per seed either way.
4. rpg-planner-ubuntu's rows and probes are all kept: the newborn-involvement count, the bodies and combatants at each fatal combat, the first tick an original entity's position diverges between arms, and deaths split by a birth in the same region within the last 30 ticks. They sit beside rows 1-3.
- The PR body discloses the rise with these numbers.

## (6) Cohort vs bodies: split in two
### 6a. Exactly +1 per birth: a bar (HARD)
- This is a bookkeeping invariant, not balance. It is code-level ruling 2 (delta = the number of newborns), measured in the real run.
- **Bar, measured on the apply side:** for every (region, tick) on head, the `population_young_births_delta` that births wrote, minus the number of newborns births added in that region at that tick. **Mismatches: 0.**
  - The delta is per region only; it carries no kind (births.py:159 at 1fa557abf). So the bar has no kind axis and doesn't read K6.
  - It compares births' own write, not the net cohort, so a cohort rebuild on the same tick can't mask or fake a mismatch. Same-tick rebuild collisions are counted and printed separately, as rpg-planner-ubuntu proposed.
- **A birth with no region is outside the bar.** births.py:159 writes no nudge when the region is None, by construction. The runner counts these births per world and seed, with the newborn's tile, and reports the count as BALANCE.
  - If the count is above 0, the PR body discloses it as "N births in no region added no cohort".
  - Whether a regionless birth should exist at all is a separate question, not this bar.
- **Not vacuous:** if head has 0 regioned births in total, it is a STOP to me, not a pass (the same rule as K8).
### 6b. Drift between the cohort count and live bodies: BALANCE
- Report per region per day, both arms: the cohort count, live bodies of each kind, and their difference. Also report the end-of-run drift.
- Drift is designed: Bible 05, "Individual-Birth Population-Pressure Nudge", says the cohort and the named entities are decoupled and never resynced. Drift also exists on main already (the open cohort truncation question). So it is no bar. Report head beside the control.
- The divergence flags (a cohort that rises while its bodies die out, or the reverse) are reported rows, not bars.

## Pre-bind check
- **(3):** touches nothing pre-bind.
- **6a and K6/K8:** it has no kind axis and counts births like K8, but it redefines neither.
- **6a and the HARD list:** it adds a bar to the HARD evidence list, which rpg-designer stated as W1-W5, K6, K6b, K8. That goes to rpg-designer as a question, and it may veto.
- **6b and the extinction line:** if the extinction line reads the cohort count rather than live bodies, drift could hide or fake an extinction. Then 6b would be pre-bind. That goes to rpg-designer as a question.

## Resolved by rpg-designer (u24), relayed by lead-planner, 2026-11-18
- **Q1: YES.** 6a joins the births HARD list (W1-W5, K6, K6b, K8, 6a) as a conservation-class accounting law. Its STOP on zero regioned births and its BALANCE side items stand.
- **Q2: live bodies.** The extinction line reads final alive bodies per species via `species_of()`: alive in >= 3 base seeds and in 0 head seeds. It never reads the regional cohort. So 6b stays BALANCE and isn't pre-bind.
- **Condition:** the Phase 1 host-read script and the Phase 2 gate row count alive bodies from `state.entities` and never read `population_young` or any region cohort counter. The births step report carries one line saying so. rpg-designer checks the read script's source at the boundary read.
