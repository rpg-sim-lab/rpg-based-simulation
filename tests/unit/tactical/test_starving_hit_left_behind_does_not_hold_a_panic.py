"""TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER (traced shape A: crowded s45 e5, t2155).

Past the starving line a hit acts only while its hitter can still reach the subject. A starving, wounded subject with a held panic whose last hitter has fallen behind
(out of reach, resting, not pursuing) no longer holds the panic: the tick falls to the need path. With the hitter adjacent the panic stands. Real frontier_living_world
seed-42 merchant 37 (wounded, gold 0, hunger 100) with predator_hunter 45 and a hunger project on inn 20003, as in test_held_panic_falls_through.py.
"""
from __future__ import annotations

from dataclasses import replace

from src.core.movement_modes import MovementMode
from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 45
INN = (40.0, 31.0)


def _scene(hunter_at, hunger=100.0, ago=3):
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[HUNTER]
    m = replace(m, navigation=replace(m.navigation, position=(30.0, 30.0), movement_mode=MovementMode.REGROUP, target=INN),
                combat=replace(m.combat, hp=10, max_hp=85, last_attacker_id=HUNTER, last_hit_tick=state.tick - ago),
                biological=replace(m.biological, hunger=hunger), inventory=replace(m.inventory, gold=0))
    h = replace(h, navigation=replace(h.navigation, position=hunter_at))
    obj = ObjectiveState(id="hunger_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id="proj_hunger_1", kind="hunger", status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    m = replace(m, strategic=replace(m.strategic, projects={proj.id: proj}, current_project_id=proj.id, current_objective_id=obj.id))
    object.__setattr__(state, "entities", {MERCHANT: m, HUNTER: h})
    return state, m


def _reason(update):
    return (update.task.payload_set or {}).get("reason") if update.task else None


def test_a_starving_wounded_subject_hit_by_a_hitter_out_of_reach_does_not_hold_a_panic_and_takes_the_need_path():
    state, merchant = _scene((30.0, 25.0))  # five tiles behind, resting
    update = TacticalDecisionSystem.evaluate_entity_intent(state, merchant)
    assert _reason(update) != "PANIC_RETREAT"  # (the tick falls through the existing order; a predator that can eat the merchant is still avoided by its own branch, which this change does not touch)


def test_the_control_with_the_old_ten_tick_hit_window_holds_the_panic(monkeypatch):
    import src.engine.tactical_threat as threat

    def old_hit_acts_on(hostile, subject, tick):  # the predicate before the reach test
        hit_tick = subject.combat.last_hit_tick
        return hit_tick is not None and subject.combat.last_attacker_id == hostile.id and tick - hit_tick <= threat.NEED_WAKE_CADENCE

    monkeypatch.setattr(threat, "_hit_acts_on", old_hit_acts_on)
    state, merchant = _scene((30.0, 25.0))
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(state, merchant)) == "PANIC_RETREAT"


def test_the_same_subject_with_the_hitter_adjacent_keeps_the_panic():
    state, merchant = _scene((30.0, 29.0))
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(state, merchant)) == "PANIC_RETREAT"


def test_below_the_starving_line_the_hit_window_still_holds_the_panic_with_the_hitter_out_of_reach():
    state, merchant = _scene((30.0, 25.0), hunger=80.0)
    assert _reason(TacticalDecisionSystem.evaluate_entity_intent(state, merchant)) == "PANIC_RETREAT"
