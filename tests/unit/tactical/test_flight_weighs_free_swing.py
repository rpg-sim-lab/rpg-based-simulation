"""TCK-20261109-A-FLIGHT-WEIGHS-THE-FREE-SWING-IT-WOULD-TAKE (divergence 2.202; Bible 02 section 7, CONFLICT-04 corollary).

A subject engaged with a hostile whose last felt blow is at least its remaining health does not flee into the free swing (COMB-009): it answers that hostile.
Scene: frontier_living_world s42, merchant 37 beside raider 24 (the real world the held-panic tests use), hunger below its line so the panic stands.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.movement_modes import MovementMode
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.apply import ApplyPath
from src.engine.candidate_selector import MovementCandidateSelector
from src.engine.tactical_flight_guard import FlightSite, flight_weighs_free_swing
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world

MERCHANT, HUNTER = 37, 24
HERE = (30.0, 30.0)


def _scene(hp=15, damage=17, attacker=HUNTER, readiness=100.0, hunter_at=(30.0, 29.0), style=1, hostile=HUNTER, extra=None):
    state = compile_world("frontier_living_world", 42)
    m, h = state.entities[MERCHANT], state.entities[hostile]
    attacker = hostile if attacker == HUNTER else attacker
    combat = replace(m.combat, hp=hp, max_hp=300, readiness=readiness, last_attacker_id=attacker, last_hit_tick=state.tick, last_hit_damage=damage)
    if style is not None:
        combat = replace(combat, action_style=style)
    m = replace(m, navigation=replace(m.navigation, position=HERE, movement_mode=MovementMode.REGROUP), combat=combat,
                biological=replace(m.biological, hunger=80.0))
    h = replace(h, navigation=replace(h.navigation, position=hunter_at))
    entities = {MERCHANT: m, hostile: h}
    if extra is not None:  # a second engaged hostile that has never hit the subject
        other_id, other_at = extra
        o = state.entities[other_id]
        entities[other_id] = replace(o, navigation=replace(o.navigation, position=other_at))
    object.__setattr__(state, "entities", entities)
    return state, m


def _decide(state, entity):
    return TacticalDecisionSystem.evaluate_entity_intent(state, entity)


def _payload(update):
    return (update.task.payload_set or {}) if update.task else {}


def _flees(update):
    return _payload(update).get("reason") == "PANIC_RETREAT"


def test_1_a_lethal_felt_blow_withholds_the_flight_and_attacks_at_full_readiness():
    state, m = _scene(hp=15, damage=17)
    up = _decide(state, m)
    assert not _flees(up) and _payload(up)["action"] == "ATTACK" and _payload(up)["target_id"] == HUNTER


def test_2_below_full_readiness_the_subject_holds_between_blows():
    state, m = _scene(hp=15, damage=17, readiness=60.0)
    up = _decide(state, m)
    assert _payload(up).get("reason") == "HOLD_BETWEEN_BLOWS" and _payload(up)["target_id"] == HUNTER


def test_3_a_blow_that_would_not_zero_it_still_flees():
    state, m = _scene(hp=18, damage=17)
    assert _flees(_decide(state, m))


def test_4_a_swing_equal_to_hp_is_lethal():
    state, m = _scene(hp=17, damage=17)
    assert not _flees(_decide(state, m))


def test_5_an_unfelt_hostile_is_not_assumed_lethal():
    for attacker in (None, 9999):
        state, m = _scene(hp=1, damage=17, attacker=attacker)
        assert _flees(_decide(state, m)), attacker


def test_7_an_evasive_flight_is_unaffected_because_the_free_swing_cannot_reach_it():
    state, m = _scene(hp=5, damage=17, style=2)
    assert _flees(_decide(state, m))


def test_8_a_felt_attacker_no_longer_engaged_does_not_hold_the_subject():
    state, m = _scene(hp=5, damage=17, hunter_at=(30.0, 27.0))
    assert _flees(_decide(state, m))


def test_6_only_the_felt_hostile_counts_among_several_engaged():
    for hp, flees in ((9, False), (11, True)):
        state, m = _scene(hp=hp, damage=10, extra=(25, (29.0, 30.0)))
        assert _flees(_decide(state, m)) is flees, hp


def test_9_when_the_attack_is_illegal_for_another_reason_the_subject_holds_its_tile():
    state, m = _scene(hp=15, damage=17, hostile=45)  # a wolf the merchant may not attack (FRIENDLY_FIRE_ILLEGAL)
    up = _decide(state, m)
    assert up.task is None and up.navigation.target_set == HERE and up.navigation.movement_mode_set is MovementMode.RETREAT


def test_a_two_attacker_free_swing_credits_the_first_attacker_with_the_total():
    """Designer ruling (a): the felt blow after a multi-attacker free swing is the swing's total, credited to attackers[0]."""
    from src.engine.combat import CombatResolutionSystem
    from src.core.updates import EntityUpdate

    state, m = _scene(hp=35, damage=None, attacker=None)
    a1, a2 = state.entities[HUNTER], replace(state.entities[HUNTER], id=25)
    object.__setattr__(state, "entities", {**state.entities, 25: a2})
    up = CombatResolutionSystem.resolve_multi_attack([a1, a2], m, state, is_opportunity_attack=True)
    hit = ApplyPath._apply_entity_update(m, EntityUpdate(entity_id=m.id, combat=up))
    assert hit.combat.last_attacker_id == HUNTER and hit.combat.last_hit_damage == up.damage_taken > 0
    # then, with only attackers[0] engaged and hp 15 against that total, there is no flight
    total = hit.combat.last_hit_damage
    state2, m2 = _scene(hp=min(15, total), damage=total)
    assert not _flees(_decide(state2, m2))


@pytest.mark.parametrize("site", list(FlightSite))
def test_10_every_flight_site_withholds_a_flight_into_a_lethal_free_swing(site):
    state, m = _scene(hp=15, damage=17)
    reason = {FlightSite.LOW_HP_RETREAT: "PANIC_RETREAT"}.get(site, site.value)
    flight = EntityUpdate(entity_id=m.id, navigation=NavigationUpdate(target_set=(30.0, 40.0), movement_mode_set=MovementMode.RETREAT),
                          task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": (30.0, 40.0), "reason": reason}))
    out = flight_weighs_free_swing(state, m, flight, site)
    assert out is not flight and _payload(out).get("action") == "ATTACK"


def test_a_move_that_is_not_a_flight_reason_is_left_alone():
    state, m = _scene(hp=15, damage=17)
    walk = EntityUpdate(entity_id=m.id, task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": (30.0, 40.0), "reason": "KEEP_DISTANCE"}))
    assert flight_weighs_free_swing(state, m, walk, FlightSite.FLEE_THREAT) is walk


def test_coverage_every_flight_reason_has_a_guarded_site_wired_in_the_tactical_pass():
    """The scope is the engine's own FLIGHT_REASONS: each has a FlightSite, and the tactical pass hands every site to the guard."""
    import inspect
    import src.engine.tactical as tactical

    source = inspect.getsource(tactical)
    sites = {site.value for site in FlightSite}
    assert MovementCandidateSelector.FLIGHT_REASONS <= sites
    for site in FlightSite:
        assert f"FlightSite.{site.name}" in source, site


def test_the_guard_reads_state_and_writes_nothing():
    state, m = _scene(hp=15, damage=17)
    before = (m.combat, m.navigation, m.task)
    _decide(state, m)
    assert (state.entities[MERCHANT].combat, state.entities[MERCHANT].navigation, state.entities[MERCHANT].task) == before
