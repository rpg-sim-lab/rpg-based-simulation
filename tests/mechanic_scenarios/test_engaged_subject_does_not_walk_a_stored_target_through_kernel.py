"""Kernel scenario (divergence 2.204): an engaged subject with a stored target off the engagement does not step into the free swing of a hostile whose felt blow is at least its hp.

Arena and staging are the CONFLICT-04 scenario's (F beside H). Neither fighter names the other as its target (so the selector's `is_engaged` test, divergence 2.89, does not stop the stored-target step), though they stand side by side, which is the engagement `resolve_move` itself uses: the shape of the traced rows. F holds a stored REGROUP target two tiles away and an idle ENTITY_ACT task; no decision lands on it (the
tactical decision is stood in by a no-op update: the cadence control, so the only thing that can move F is the movement phase walking its stored target). F's hp is 20 and its
last felt blow, from H, was 23. Control arm: the held-step check is switched off, so F walks off and pays the opportunity attack (the def2 s45 #5 shape).
"""
from __future__ import annotations

from dataclasses import replace

import src.engine.movement as movement
from src.core.movement_modes import MovementMode
from src.core.state import TaskComponent
from src.core.updates import EntityUpdate
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world, empty_inventories
from tests.mechanic_scenarios.test_conflict04_fighter_holds_between_blows import ADJ, F, F_POS, H, NON_CAUTIOUS, WORLD_ID, _stage, _trace

STORED_TARGET = (3.0, 1.0)  # two tiles from F at (1, 1), away from H at (1, 2): the step to (2, 1) leaves the engagement


def _state():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=ADJ, need_profile=NON_CAUTIOUS, readiness=100.0)
    f = state.entities[F]
    f = replace(f, task=TaskComponent(work_kind="ENTITY_ACT", payload={}),
                navigation=replace(f.navigation, target=STORED_TARGET, movement_mode=MovementMode.REGROUP),
                combat=replace(f.combat, hp=20, last_attacker_id=H, last_hit_tick=0, last_hit_damage=23))
    h = state.entities[H]
    h = replace(h, task=TaskComponent(work_kind="ENTITY_ACT", payload={}))  # neither names the other as its target: the movement layer's CONFLICT-04 test (is_engaged) does not hold, as in the traced rows
    object.__setattr__(state, "entities", {**state.entities, F: f, H: h})
    return state


def _no_decision_for_f(monkeypatch):
    real = TacticalDecisionSystem.evaluate_entity_intent

    def decide(st, entity, *a, **kw):
        return EntityUpdate(entity_id=entity.id) if entity.id == F else real(st, entity, *a, **kw)

    monkeypatch.setattr(TacticalDecisionSystem, "evaluate_entity_intent", staticmethod(decide))


def test_engaged_subject_does_not_walk_a_stored_target_into_a_felt_lethal_swing(monkeypatch):
    _no_decision_for_f(monkeypatch)
    out = _trace(_state(), 3)
    assert {r["f_pos"] for r in out["rows"]} == {F_POS}, "F walked its stored target off the engagement"
    assert out["oa_on_f"] == [], "an opportunity attack landed on F"


def test_control_without_the_held_step_f_walks_off_and_pays_the_opportunity_attack(monkeypatch):
    _no_decision_for_f(monkeypatch)
    monkeypatch.setattr(movement, "felt_lethal_attacker", lambda state, entity: None, raising=False)
    out = _trace(_state(), 3)
    assert {r["f_pos"] for r in out["rows"]} != {F_POS}, "F did not walk"
    assert len(out["oa_on_f"]) >= 1, "walking off paid no opportunity attack"
