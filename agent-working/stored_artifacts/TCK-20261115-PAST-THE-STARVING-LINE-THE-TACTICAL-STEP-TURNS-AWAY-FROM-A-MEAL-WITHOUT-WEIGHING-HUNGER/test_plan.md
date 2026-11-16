---
status: historical
layer: combat
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER
phase: done
date: 2026-11-15
tags: []
---

# Test plan

## New (the designer's 7)
| # | where | case | expect |
|---|---|---|---|
| 1 | tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py | hunger >= 95, last attacker at Manhattan 5, task None, hit 3 ticks ago | not acting |
| 2 | same | same, adjacent (distance 1) | acting |
| 3 | same | distance 5, hostile task PURSUE with target_id = subject | acting (term a) |
| 4 | same | hunger < 95, distance 5, hit within 10 ticks | acting (unchanged) |
| 5 | same | hunger >= 95, hitter range 4 at distance 3 | acting |
| 6 | tests/unit/tactical/ (new file beside test_held_panic_falls_through.py) | starving + fleeing + held panic, hitter out of reach -> need path; hitter adjacent -> PANIC_RETREAT stands | as stated |
| 7 | tests/integration/ (real kernel, built fixture, modelled on test_starving_wounded_merchant_eats_through_the_real_kernel.py) | starving wounded subject 1 tile from an inn, hitter moves >= 3 tiles away | eats within 2 ticks; fails on the old predicate |

Boundary cases to add to the unit file (cheap): hunger exactly 95.0 (at the line counts as past), distance exactly max(1, range) (reach inclusive), hit exactly 10 ticks ago and 11 ticks ago past the line.

## Existing tests to run (read, never edited to pass)
tests/unit/engine/test_acting_hostile_is_an_act_not_a_state.py; tests/unit/tactical/ (test_surv07_precedence_grid.py, test_surv07_hunt_project_grid.py, test_held_panic_falls_through.py, test_flight_weighs_free_swing.py); tests/unit/strategic/test_retreat_ends_with_its_threat.py; tests/unit/ai/test_need_scorers.py, test_retreat_escalates_on_the_need_scale.py, test_opening_steps.py; tests/unit/movement/test_felt_lethal_free_swing_step.py; tests/mechanic_scenarios/test_flight_weighs_free_swing_through_kernel.py, test_engaged_subject_does_not_walk_a_stored_target_through_kernel.py; tests/integration/observability/test_starving_wounded_merchant_eats_through_the_real_kernel.py; tests/unit/tools/test_mechanism_registry_completeness_check.py.
All single process (-n 0), only with >= 3500 MB available and nothing measuring.

## Out of this build
Paired measurement (3 worlds x s42-46 x 5000t), rows r1/r2, V3 cell re-read and rpg_gate_known.yaml: after HOLD stage 2, rpg-planner's slot.
