---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES
phase: open
date: 2026-11-22
tags: []
---

# TCK-20261122-TOWN-TILE-HEALING-IGNORES-STARVATION-SO-A-STARVING-BODY-IN-TOWN-NEVER-DIES

## Title
Town-tile healing has no hunger check, so a starving body standing in town regains every HP the starvation drain takes and never dies

## Status
INPROGRESS

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by rpg-designer's recount of the #781 stage-2 trace, 2026-11-22.
- Trace kit v3: spy 67bb643f, controls 329a3000, run b2c44eef. OUT /mnt/data2/rpg-measure/freemeal_pre/trace_full_v3. S9 #715 7075116023, amended 7075268236.
- Recount: /mnt/data2/rpg-measure/freemeal_pre/trace_full_v3_designer_recount/recount.out, sha256 be9b21bd….

What it found (executed):
- In the fix arm, urban_political s42, there are 5398 subject-ticks at prior hunger >= 95.
- The tree's own formula, starvation.hp_loss (1 HP when (tick + eid) % round(6000 / max_hp) == 0), predicts 89 losses. 89 were observed, an exact match. So the passive drain does reach them.
- 80 ticks show hp +1, each with upd_combat.hp_delta = 1 (outcome SURVIVE), a few ticks after each loss. For eid 3: losses at 1917/1977/2037…, gains at 1921/1981/2041….
- So hp oscillates at its maximum, and 7 humans live 18,500-22,100 ticks past the starving line.

The writer (inspected, 89a37bb2):
- The only +1 CombatUpdate writer in src is src/systems/town_resolution.py:93-99, "Part A: Town Logic (Healing)". A living body on a town tile with hp < max_hp gets CombatUpdate(hp_delta=PASSIVE_HEAL_AMT=1) (:64), with NO hunger check.
- The other positive writers are the bed (+5, on a paid transfer) and the vitality AP (+10).
- Town-tile membership per row is inferred from this, not read directly.

This contradicts the law. docs/mechanics/01_entity_anatomy.md Staged Starvation (owner decision 36) and Natural Healing (owner decision 42) both say NOTHING heals at or past the starving line (natural_healing.hp_gain returns 0 at hunger >= 95).

It is PRE-EXISTING: the same lines are at base 85770a225 (:64, :99). #781 only exposes it, because in base nobody starved while standing in town.

## Scope
1. Town-tile healing obeys the same need stages as natural healing: no heal at or past the starving line. Preferably it calls the one healing rule (natural_healing) rather than keeping a second heal law. rpg-designer's ruling of direction, 2026-11-22.
2. Tests, each with a failing control:
   - a starving body (hunger >= 95) on a town tile loses hp on the starvation schedule and gains nothing;
   - a non-starving body on a town tile still heals as today;
   - the boundary at hunger 94 vs 95.
3. Docs in the same change: a Bible line (ch01 healing), a divergence entry (Bug Fix) and a parity entry update.
4. Hash change disclosed. It is expected wherever a starving body stood on a town tile.

## Out of Scope
- #781's earn_then_buy never-exit opening step. That is a separate defect, found in the same recount and handled under TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1, or its own ticket after lane A's code read.
- Retuning PASSIVE_HEAL_AMT or the inn/bed heal amounts.

## Acceptance Criteria
1. No healing source grants hp to a body at or past the starving line, except the explicitly paid services if rpg-designer rules them in or out. State which.
2. The tests above pass, and each has a failing control.
3. Bible, divergence and parity are updated together.
4. #781's W urban cell re-runs with kit v3.5 after both this fix and the earn_then_buy fix, and rpg-designer re-reads guard (ii).

## Related Tickets
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#781; it depends on this ticket and stays blocked until it lands)
- TCK-20261011-EVERY-LIVING-KIND-HEALS-NATURALLY-FASTER-AT-REST-ROW-65 (owner decision 42, natural healing)

## Related Docs
- docs/mechanics/01_entity_anatomy.md (Staged Starvation D36, Natural Healing D42)
- docs/guidelines/intentional_divergences.md 2.116
- docs/world_rules/life-body/survival-needs.md SURV-02

## Related Stored Artifacts
- /mnt/data2/rpg-measure/freemeal_pre/trace_full_v3/ and trace_full_v3_designer_recount/

## Related Code Areas
- src/systems/town_resolution.py (Part A healing, PASSIVE_HEAL_AMT)
- natural_healing (hp_gain) and starvation (hp_loss)

## Assumptions / Open Questions
- Whether a paid bed (+5) or inn rest should heal a starving body is for rpg-designer to rule. The town-tile passive heal clearly should not.
- The "on a town tile" link for each trace row is inferred from the only matching writer.

## Durable state, lifecycle and clocks
None new. It changes a heal rule on existing hp.

## Implementation Notes
Option A (designer): gate on post-accrual hunger vs the one STARVING_LINE. Helper hunger_after_accrual shared with apply.py. Writer path is src/engine/town_resolution.py.

## Test Summary

## Files Changed
src/engine/town_resolution.py, src/engine/biological_needs.py, src/engine/apply.py, tests/unit/engine/test_town_heal_starvation_line.py, docs/mechanics/01_entity_anatomy.md, docs/guidelines/intentional_divergences.md (2.220), docs/parity_ledger/progression.yaml (PROG-138)

## Completion Summary
