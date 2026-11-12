"""TCK-20261110-A-NON-FLIGHT-MOVE-OFF-ENGAGEMENT-WALKS-INTO-A-KNOWN-LETHAL-FREE-SWING (divergence 2.204; Bible 02 section 7, CONFLICT-04 corollary).

`MovementSystem.resolve_move` does not take a step that would give the free swing (COMB-009) to an engaged hostile the subject has felt will finish it, whatever
chose the step (a flight, an engage or bracketing step, a stored strategic target). The held step leaves state as a legality-blocked step does.
Scene: frontier_living_world s42, merchant 37 beside raider 24 (the 2.202 tests' world), the merchant's stored target two tiles away from the engagement.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.enums import ReasonCode
from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate
from src.engine.movement import MovementSystem
from src.engine.movement_cache import MovementPlanCache
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 24
HERE = (30.0, 30.0)
TARGET = (30.0, 33.0)  # away from the hunter at (30, 29): a step to (30, 31) leaves the engagement


def _scene(hp=15, damage=17, attacker=HUNTER, hunter_at=(30.0, 29.0), style=1, extra=None):
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[HUNTER]
    combat = replace(m.combat, hp=hp, max_hp=300, readiness=100.0, last_attacker_id=attacker, last_hit_tick=state.tick, last_hit_damage=damage, action_style=style)
    m = replace(m, navigation=replace(m.navigation, position=HERE, target=TARGET, step_ready_tick=0), combat=combat)
    h = replace(h, navigation=replace(h.navigation, position=hunter_at))
    entities = {MERCHANT: m, HUNTER: h}
    if extra is not None:  # a second hostile beside the subject that has never hit it
        other_id, other_at = extra
        o = state.entities[other_id]
        entities[other_id] = replace(o, navigation=replace(o.navigation, position=other_at))
    object.__setattr__(state, "entities", entities)
    object.__setattr__(state, "movement_cache", MovementPlanCache())
    return state, m


def _move(state, entity, mode=MovementMode.REGROUP):
    return MovementSystem.resolve_move(state, entity, TARGET, mode)[entity.id]


def test_step_is_held_when_an_engaged_hostile_has_felt_lethal():
    state, m = _scene(hp=15, damage=17)
    up = _move(state, m)
    assert up.new_position is None and not up.moved_this_tick and up.combat is None and up.stamina_update is None
    assert up.navigation.wait_count_delta == 0 and not up.navigation.target_clear and not up.navigation.clear_target
    assert up.navigation.failure_reason == ReasonCode.FELT_LETHAL_FREE_SWING


def test_step_is_held_for_a_decided_reposition_step():
    state, m = _scene(hp=15, damage=17)
    up = _move(state, m, MovementMode.REPOSITION)
    assert up.new_position is None and up.combat is None
    assert up.navigation.failure_reason == ReasonCode.FELT_LETHAL_FREE_SWING


def test_step_is_taken_when_the_felt_swing_is_under_hp():
    state, m = _scene(hp=18, damage=17)
    up = _move(state, m)
    assert up.new_position is not None and up.moved_this_tick
    assert up.combat is not None and up.combat.hp_delta < 0  # the free swing fires, as on main


def test_step_is_taken_when_the_felt_attacker_is_not_engaged():
    other = next(eid for eid in compile_world("frontier_living_world", 42).entities if eid not in (MERCHANT, HUNTER))
    state, m = _scene(hp=15, damage=17, attacker=other)  # the felt attacker is elsewhere; the engaged hunter has never hit the subject
    up = _move(state, m)
    assert up.new_position is not None and up.combat is not None and up.combat.hp_delta < 0


def test_step_is_taken_with_no_felt_blow():
    state, m = _scene(hp=15, damage=None, attacker=None)
    up = _move(state, m)
    assert up.new_position is not None and up.combat is not None and up.combat.hp_delta < 0


def test_evasive_flight_is_unaffected():
    state, m = _scene(hp=15, damage=17, style=2)
    up = _move(state, m, MovementMode.RETREAT)
    assert up.new_position is not None and up.moved_this_tick
    assert up.combat is None  # the free swing cannot reach an evasive retreat, as on main


def test_held_step_matches_a_blocked_step():
    """The held update has the blocked-step shape (movement.py: the not-success return) with only failure_reason set: no step, no stamina, no cognition write, no property tag."""
    state, m = _scene(hp=15, damage=17)
    up = _move(state, m)
    expected = EntityUpdate(entity_id=MERCHANT, navigation=NavigationUpdate(failure_reason=ReasonCode.FELT_LETHAL_FREE_SWING, wait_count_delta=0))
    assert up == expected


def test_held_step_leaves_the_plan_cache_as_a_blocked_step_does():
    state, m = _scene(hp=15, damage=17)
    _move(state, m)
    assert len(state.movement_cache._cache) == 0
    state2, m2 = _scene(hp=18, damage=17)  # the same scene with a step that is taken
    _move(state2, m2)
    assert len(state2.movement_cache._cache) == 1
