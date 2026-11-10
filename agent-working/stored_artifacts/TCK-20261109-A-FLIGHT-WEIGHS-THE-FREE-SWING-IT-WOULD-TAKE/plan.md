---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE
artifact_type: plan
---

# Plan

Written at close from the work as it landed; the design lives in the designer spec (`.claude/handover/drafts/rpg-designer-flight-weighs-free-swing-design.md`) and the planner rulings recorded in the ticket.

1. Field and carrier commit (`aacefef9c`): `CombatUpdate.hit_damage_set`, `CombatComponent.last_hit_damage` (written under the same `hit_landed` condition as `last_hit_tick`), canonical dict key, digest `flat-sha256-v4`, the shared `is_evasive_flight` predicate. Proof (i): stripped digest on crowded s42 equals base.
2. Guard commit (`e0931a3af`): `flight_weighs_free_swing(state, entity, update, site)` in `src/engine/tactical_flight_guard.py`, called at the six `FLIGHT_REASONS` emission sites; response ATTACK, else held swing, else in-place hold.
3. Docs: Bible 02 section 7, CONFLICT-04 corollary, divergence 2.202, COMB-351 and the COMB-009 note.
4. Filing: the double `resolve_attack` per tick (P2).
5. Measurement: arm 1 (guard alone, crowded and urban, 5 seeds x 5000, paired), then a Tier 2 trace on 31 subjects. Arm 2 (hit-wake on top) is a later ticket.
