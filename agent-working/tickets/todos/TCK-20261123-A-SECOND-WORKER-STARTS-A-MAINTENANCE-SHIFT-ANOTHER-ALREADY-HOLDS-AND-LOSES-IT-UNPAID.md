---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20261123-A-SECOND-WORKER-STARTS-A-MAINTENANCE-SHIFT-ANOTHER-ALREADY-HOLDS-AND-LOSES-IT-UNPAID
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-SECOND-WORKER-STARTS-A-MAINTENANCE-SHIFT-ANOTHER-ALREADY-HOLDS-AND-LOSES-IT-UNPAID

## Title
A second worker starts a maintenance shift that another worker already holds, and loses it unpaid when the other finishes first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
This is the cause of #995's one remaining P2 HARD hit, per rpg-designer's h3 trace read: freemeal_pre/trace_h3_designer_read/READ.md, kit v7, trace of 13844fee8 at urban_political s42 (executed reads; code inspected at 13844fee8).

What the trace shows for human 3:
- Its gold was 0 after the t16548 meal. From t17777 its only way was WORK_SHIFT at blacksmith 20002.
- Blacksmith 20002 is maintenance-only: hires_for_pay is false, and it needs 1 shift per upkeep period.
- Three held shifts ended UNPAID: 17798-17953, 17988-18170 and 18218-18405, 527 ticks in all.
  - Each ended on the tick `maintenance_shifts_done` went 0 → 1, when another worker finished the single needed shift.
  - `serves()` then turns false, and `work_update` resets the interaction with no wage (work_shift.py:146-147).
- The 4th shift paid 6.
- The 619 ticks over the line were 188 working, plus 421 in a collapse sleep, plus 9 walking.
- Counterfactual: if shift 1 had paid, there would have been no crossing.

The defect: shift_startable / can_pay_shift answer True for a single maintenance slot that another worker already HOLDS. Finishing the slot then voids every other started shift. This also breaks divergence 2.151 ("a shift is interrupted only by a present threat").

## Scope
1. rpg-designer's design, which is a DRAFT until the owner rules. Sketch: main-checkout .claude/handover/drafts/rpg-designer-t1-maintenance-claim-sketch.md, sha a2ad8770.
   - A typed `BuildingState.maintenance_holders` (MaintenanceHold(entity_id, shift_start)), granted at the shift's first tick in the apply step, the same pattern as F3 grant_beds.
   - One predicate, `maintenance_slot_free`, read by every start-side reader.
   - A taken slot closes that way for the subject, which moves to its next way.
   - A started shift is never voided by the slot completing.
   - Paid-hire buildings: unchanged in effect, except that the maintenance wage goes to the slot's holder.
2. Four owner questions, with the designer's recommended option first:
   - hold the slot / pro-rata / as is;
   - a refused worker moves on / waits;
   - the maintenance wage goes to the holder / the first finisher;
   - holds carry over the upkeep reset / are cleared.
3. Mechanic-scenario tests. The h3 repro is test 1. Add a failing control on 13844fee8.
4. Bible ch03 EXCH-02, plus the parity entry for ruling 66 and the divergence 2.151 note, updated in the same change.
5. Re-measure the w995 cells with hungerkit v3.5 after the fix. The 3 withheld grade re-pins land only if P2 reads clean.

## Out of Scope
- #995's re-point (its fix works: trace point 4).
- Fatigue with no bed way (T2: TCK-20261123-AN-EXHAUSTED-BODY-WITH-NO-BED-SLEEPS-ONLY-BY-COLLAPSE).
- The "cut a held shift" option: NOT asked. The designer recommends against it, because cutting shifts is what caused the loss.

## Acceptance Criteria
1. The owner's answers to the 4 questions are recorded, with their #715 ids, before any code.
2. A second worker never starts a maintenance shift on a slot another worker holds. A started shift ends only by its own completion or a present threat (tests plus a failing control).
3. The w995 cells re-measure P2 clean, or each remaining hit is attributed with a cause.
4. Bible, parity and divergence are in parity.

## Related Tickets
- #995 / TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (the exposer); its known entry cites this ticket, if the owner picks option B
- TCK-20261123-AN-EXHAUSTED-BODY-WITH-NO-BED-SLEEPS-ONLY-BY-COLLAPSE

## Related Docs
- docs/mechanics/03_economic_laws.md (EXCH-02); docs/guidelines/intentional_divergences.md (2.151)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/freemeal_pre/trace_h3_designer_read/ (READ.md); trace_h3_out/ (kit v7, S9 on #715)

## Related Code Areas
- src/engine/work_shift.py (shift_startable, can_pay_shift, work_update:146-147); src/engine/serves.py; src/core/state.py (BuildingState); the apply step

## Assumptions / Open Questions
- The other worker was not traced (near ids 25/27, 10/25, 25). The design does not depend on who it was.
- Order: the M1 backlog, right after #995/#996. If the owner picks option B for #995, this ticket owns #995's P2 known entry and its expiry.

## Durable state, lifecycle and clocks
`maintenance_holders` is durable building state: a typed model, granted in apply, released at shift end or the holder's death, kept or cleared over the upkeep reset per the owner's answer, inspected in the building read model, and tested. To be filled at scope.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
