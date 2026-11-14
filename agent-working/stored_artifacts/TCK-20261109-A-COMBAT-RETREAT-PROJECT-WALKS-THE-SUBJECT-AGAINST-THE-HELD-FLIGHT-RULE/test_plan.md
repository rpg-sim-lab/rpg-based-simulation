---
status: historical
layer: strategy
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE
phase: done
date: 2026-11-12
tags: []
---

# Test plan

Unit rows (new file under tests/unit/engine/ or movement, plus a kernel row in tests/mechanic_scenarios/):
- a perceived hostile orthogonally adjacent, neither side naming the other, no decision this tick: the stored target takes no step (`movement_target` returns None);
- a hostile adjacent but not perceived as hostile: the stored target walks;
- a decided ENTITY_MOVE this tick: the step is taken;
- a decided flight held as ENTITY_MOVE (`is_decided_flight`): the step is taken;
- `move_ends_here`: a held non-flight ENTITY_MOVE beside a perceived unnamed hostile ends (if the designer rules it flips);
- the Decision-32 wake still fires for an unnamed perceived adjacent hostile (`unengaged_adjacent_hostile` unchanged);
- 2.84 (an ENTITY_ACT holder with a payload does not walk) and 2.204 (felt-lethal hold) unchanged.

Existing rows that must stay green: tests/mechanic_scenarios/test_conflict04_movement_layer.py (invariant test hooks `engaged_adjacent_hostile` by name), tests/unit/engine/test_diagonal_melee_pair_strikes.py, tests/unit/engine/test_notice_unengaged_hostile.py, tests/mechanic_scenarios/test_decision32_notice_and_decide.py, tests/mechanic_scenarios/test_entity_death_authority_boundary.py (corpus DEFEAT test).

Gates before any push: code-health, mypy, tests/architecture, the scoped set, `generate_registry.py --check`.

Measurement is in plan.md step 4.

## Outcome

The tests in this plan were written on the parked branch only (its scoped set ended at 1 failed, 1248 passed: the corpus DEFEAT test, deliberately red). None lands on main; this close changes no src or tests.
