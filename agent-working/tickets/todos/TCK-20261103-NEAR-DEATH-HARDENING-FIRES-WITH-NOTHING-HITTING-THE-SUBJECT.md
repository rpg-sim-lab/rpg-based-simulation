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
Found by rpg-designer on 2026-11-03 from crowded s45 e34, whose max hp grew 150 to 310 while it was starving (the #828 composition check, V3 red). `NearDeathHardeningPhase` (src/engine/pipeline_phases/hardening.py, read at ca9ebe7c6) takes any surviving CombatUpdate with projected hp at or below 10% of max and adds `max_hp_delta=5`, `permanent_max_hp_bonus_delta=5` and a "near_death" emotion. Nothing in the part read tests hp_delta < 0, while the law says it follows surviving a hit.

rpg-planner-ubuntu reports this proven on rows (relayed by lead-planner-u24, not checked by rpg-planner): about 40 grants on e34 with nothing hitting it, on both trees, from the town heal (src/engine/town_resolution.py Part A, `hp_delta=PASSIVE_HEAL_AMT`).

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
- e34 trace pair and rows: rpg-planner-ubuntu, #828 composition evidence (path to be confirmed when #828 is pushed). Rows past t2000 are not to be used until ubuntu's t2131 vs u24's t2101 death-tick difference is resolved (lead-planner-u24, 2026-11-03).

## Related Code Areas
- src/engine/pipeline_phases/hardening.py
- src/engine/town_resolution.py (Part A healing)
- src/engine/pipeline.py

## Assumptions / Open Questions
- Whether sources other than the town heal also reach it. Count 1 states it.
- The order in rpg-planner's queue is decided after the counts. It needs an owner yes for dispatch.
- The grant lowers hp share, so it may interact with the row 88 lines. Hypothesis only.

## Implementation Notes
2026-11-03 rpg-designer, on ubuntu's rows (relayed, not checked by rpg-planner):
- About 40 of base e34's 53 grants landed with no hit. Both trees, not part of #828.
- Counts also split by kind, with max hp reached and near_death firings.
- Fix lean: require hp_delta < 0, as the law says. Check whether 01_entity_anatomy.md:54 and the two parity rows claim otherwise.
- Town tiles only by this path. It may inflate panic counts near towns and shortens hp_loss_period on survivors, so ENG's starving and panic numbers carry it on both arms. No ENG re-run for it: ENG's row notes it was measured on a tree with this defect.
- Order: rpg-designer would put it ahead of LOW-HP-RETREAT, whose panic counts it muddies. rpg-planner's call, with the owner's yes for dispatch.

## Test Summary

## Files Changed

## Completion Summary
