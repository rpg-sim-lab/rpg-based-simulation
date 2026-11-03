---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT
phase: open
date: 2026-11-03
tags: []
---

# TCK-20261103-NEAR-DEATH-HARDENING-FIRES-WITH-NOTHING-HITTING-THE-SUBJECT

## Title
Near-death hardening grants permanent max hp and a near_death emotion on a heal, with nothing hitting the subject: counts first

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-designer on 2026-11-03 from crowded s45 e34, whose max hp kept growing while it was starving (the #828 composition check, V3 red; base 150 to 350 by t2000). `NearDeathHardeningPhase` (src/engine/pipeline_phases/hardening.py, read at ca9ebe7c6) takes any surviving CombatUpdate with projected hp at or below 10% of max and adds `max_hp_delta=5`, `permanent_max_hp_bonus_delta=5` and a "near_death" emotion. Nothing in the part read tests hp_delta < 0, while the law says it follows surviving a hit.

rpg-planner-ubuntu reports this proven on rows (relayed by lead-planner-u24, not checked by rpg-planner), for base e34 up to t2000: 40 grants, of which 37 have hp rising and only 3 fall on a new last-hit tick (t1521, t1644, t1667); 29 grants come after t1667 with no hit at all since t1666. On both trees, from the town heal (src/engine/town_resolution.py Part A, `hp_delta=PASSIVE_HEAL_AMT`).

Why it matters, as a hypothesis until counted: a low-hp body in a town gains max hp and panic repeatedly with nothing hitting it, which lowers its hp share, keeps it under the hp lines and may hold it in panic while it starves. The emotional panic counts in the SURV-07 reading may be inflated by it.

## Scope
Counts first, with no fix shape before the counts and rpg-designer's ruling:
1. Per run on the standard seeds and worlds: grants split by hp_delta < 0 and hp_delta >= 0, and by the source of the CombatUpdate (town heal, other heal, other).
2. Panic ticks and deaths among subjects with non-hit grants, compared with subjects with hit grants only.
3. Max hp gained through non-hit grants: per subject, largest and total.
4. State the law text against the code: docs/mechanics/01_entity_anatomy.md:54, the near-death parity rows, and tests/mechanic_scenarios/test_emotion_near_death_hardening.py (does any test pin a non-hit grant).

rpg-designer's lean, to be confirmed after the counts: real hits only.

## Out of Scope
- The #828 landing: this ticket does not hold it (rpg-designer).
- The hp<15% PANIC_RETREAT writer and its reason rename (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE).
- Retuning the grant size or the 10% line.

## Acceptance Criteria
- Counts 1-4 are reported and rpg-designer rules on the shape.
- If a fix follows: unit tests for a heal below the line (no grant), a hit survived below the line (grant unchanged); its own measured step with deaths paired under the death-STOP bar; Bible ch.01 and the parity rows updated in the same change; a divergence entry if the behaviour changes.
- Hot-loop: yes if fixed (the phase runs per combat update applied). Under the perf pause (#715 6556861718), timing is NOT MEASURED and is covered by checkpoint (a).

## Related Tickets
- TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED (the SURV-07 panic reading)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (#828; e34 evidence)
- TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE

## Related Docs
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/social_narrative.yaml (`test_near_death_hardening`)
- docs/plans/systemic_world/owner_decision_memo.md rows 83 and 88

## Related Stored Artifacts
- e34 trace pair and rows: rpg-planner-ubuntu, #828 composition evidence (path to be confirmed when #828 is pushed). Ubuntu's trace rows past t2000 describe `_run_engine` only (e34 death t2131), not the reference; the pinned build_kernel's e34 death at t2101 is the reference (lead-planner-u24, 2026-11-03; cause of the runner difference open).

## Related Code Areas
- src/engine/pipeline_phases/hardening.py
- src/engine/town_resolution.py (Part A healing)
- src/engine/pipeline.py

## Assumptions / Open Questions
- Whether sources other than the town heal also reach it. Count 1 states it.
- The order in rpg-planner's queue is decided after the counts. It needs an owner yes for dispatch.
- The grant lowers hp share, so it may interact with the row 88 lines. Hypothesis only.

## Implementation Notes
- 2026-11-03 second case (rpg-planner-ubuntu's pinned e30 trace, crowded s42 base, end hash equal to the set; relayed by rpg-designer): 20 grants, 14 on +1 heal ticks, max hp 120 to 220.
2026-11-03 rpg-designer, on ubuntu's rows (relayed, not checked by rpg-planner):
- Use only the corrected count in the Request Summary (37 of 40; 29 since t1666). Earlier "53", "47" and "about 40 with no hit" are NOT usable: past t2000 ubuntu's trace is a `_run_engine` run, which leaves the pinned reference between t2000 and t2100 (the pinned replay on both hosts has e34 dead at t2101; `_run_engine` has t2131). Both trees, not part of #828.
- Counts also split by kind, with max hp reached and near_death firings.
- Fix lean: require hp_delta < 0, as the law says. Check whether 01_entity_anatomy.md:54 and the two parity rows claim otherwise.
- Town tiles only by this path. It may inflate panic counts near towns and shortens hp_loss_period on survivors, so ENG's starving and panic numbers carry it on both arms. No ENG re-run for it: ENG's row notes it was measured on a tree with this defect.
- Order: rpg-designer would put it ahead of LOW-HP-RETREAT, whose panic counts it muddies. rpg-planner's call, with the owner's yes for dispatch.

## Test Summary

## Files Changed

## Completion Summary
