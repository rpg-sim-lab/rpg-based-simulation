"""Kernel scenario (divergence 2.202): a hurt, cautious fighter engaged with a hostile whose felt blow exceeds its hp does not flee into the free swing.

Arena and staging are the CONFLICT-04 scenario's (`mechanic_scenario_combat_judgement_withdrawal`, F beside H). Control arm: nothing guards the free swing (the flight guard and the step
guard of divergence 2.204 are both switched off), so the same fighter leaves and pays the opportunity attack (CP-S18's control). Guard arm: it stays on its tile, takes no
opportunity attack, and answers H. Backstop arm: with only the flight guard off, the step guard in `resolve_move` holds the flight.
(The control was edited by TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING because that ticket changes its premise: the step guard now also
stops the flight the flight guard no longer withholds. It is not an edit to pass a gate.)
"""
from __future__ import annotations

from dataclasses import replace

import src.engine.movement as movement
import src.engine.tactical as tactical
from src.core.enums import ReasonCode
from src.engine.movement import MovementSystem
from tests.helpers.scenario import compile_world, empty_inventories
from tests.mechanic_scenarios.test_conflict04_fighter_holds_between_blows import ADJ, CAUTIOUS, F, F_POS, H, WORLD_ID, _stage, _trace

HP, FELT = 40, 60


def _state():
    state = _stage(empty_inventories(compile_world(WORLD_ID)), h_pos=ADJ, need_profile=CAUTIOUS, readiness=100.0, hp=HP)
    f = state.entities[F]
    felt = replace(f, combat=replace(f.combat, last_attacker_id=H, last_hit_tick=0, last_hit_damage=FELT))
    object.__setattr__(state, "entities", {**state.entities, F: felt})
    return state


def test_control_without_the_guard_the_fighter_flees_into_the_free_swing(monkeypatch):
    monkeypatch.setattr(tactical, "flight_weighs_free_swing", lambda state, entity, update, site: update)
    monkeypatch.setattr(movement, "felt_lethal_attacker", lambda state, entity: None)  # nothing guards the free swing
    out = _trace(_state(), 12)
    assert {r["f_pos"] for r in out["rows"]} != {F_POS}, "the cautious fighter did not leave"
    assert len(out["oa_on_f"]) >= 1, "leaving paid no opportunity attack"


def test_with_only_the_flight_guard_off_the_step_guard_holds_the_flight(monkeypatch):
    monkeypatch.setattr(tactical, "flight_weighs_free_swing", lambda state, entity, update, site: update)
    real = MovementSystem.__dict__["resolve_move"].__func__
    held = []

    def spy(state, entity, target, *a, **kw):
        res = real(state, entity, target, *a, **kw)
        upd = res.get(entity.id)
        if entity.id == F and upd is not None and upd.navigation is not None and upd.navigation.failure_reason == ReasonCode.FELT_LETHAL_FREE_SWING:
            held.append(state.tick)
        return res

    monkeypatch.setattr(MovementSystem, "resolve_move", staticmethod(spy))
    out = _trace(_state(), 12)
    assert held, "the step guard never held the flight"
    assert {r["f_pos"] for r in out["rows"]} == {F_POS}, "the fighter stepped off the engagement"
    assert out["oa_on_f"] == [], "a free swing landed on the held fighter"


def test_guard_the_fighter_stands_and_answers_the_hostile_it_has_felt():
    out = _trace(_state(), 12)
    assert {r["f_pos"] for r in out["rows"]} == {F_POS}, "the fighter stepped off the engagement"
    assert out["oa_on_f"] == [], "an opportunity attack landed on the holding fighter"
    assert any(d["eid"] == F and d["action"] == "ATTACK" for d in out["decisions"]), "the fighter never answered the hostile"


def test_guard_two_runs_are_identical():
    a, b = _trace(_state(), 12), _trace(_state(), 12)
    assert [(r["f_pos"], r["f_hp"], r["h_hp"]) for r in a["rows"]] == [(r["f_pos"], r["f_hp"], r["h_hp"]) for r in b["rows"]]
