"""PERC-02a review findings (rpg-designer ruling, #955): P1-1 the clock and P1-2 lodging.

P1-1: an attack's legality (`hostility.attack_allowed`) and a feeding kill (`hostility.is_feeding_kill`) judge perception by the same night clock as the tactical decision
(`is_night(state.world_time)`), and `night` and `tick` are required arguments of `relation`, `perceived_hostile`, `attack_allowed` and `perceives`: a forgotten one fails at the call.
P1-2: a held pursuit target is kept by `appraisal.perceives`, the one eligibility rule (alive, neither body lodged, then the gate), not by a gate call of its own.

The pair is a hungry wild dragonkin (large, medium vision, no night vision) and a still human (medium visibility) two tiles away, in the compiled `frontier_living_world`: by day the
dragonkin sees it (PREDATION), by night its vision counts two rungs lower and a still body is silent, so it does not."""
from __future__ import annotations

import inspect
from dataclasses import replace

import pytest

from src.core.calendar import is_night
from src.core.enums import ReasonCode
from src.engine.appraisal import HUNT_HUNGER, Relation, perceives
from src.engine.hostility import attack_allowed, is_feeding_kill, perceived_hostile, relation
from src.engine.legality import LegalityServiceV2
from src.engine.tactical import _held_target_in_view
from tests.helpers.clock import DAY_WORLD_TIME
from tests.helpers.scenario import compile_world
from src.core.species import species_of

NIGHT_WORLD_TIME = 0
assert is_night(NIGHT_WORLD_TIME) and not is_night(DAY_WORLD_TIME)


@pytest.fixture(scope="module")
def world():
    return compile_world("frontier_living_world", 42)


def _first(state, species):
    return next(e for e in state.entities.values() if species_of(e) == species)


NIGHT_DX = 8.0  # PERC 3a: a still medium body is seen at night out to 6 tiles (divergence 2.229), so the night rows that need an UNSEEN target stand 8 tiles off (the relation check precedes the range check, so the refusal they assert is still the one reached)


def _pair(world, world_time, dx=2.0):
    """(state, predator, prey): a hungry wild dragonkin (the wolf's wild body re-kinded: wild faction, no night vision) `dx` tiles from a still human."""
    wolf, human = _first(world, "wolf"), _first(world, "human")
    props = dict(wolf.identity.properties or {})
    props["species_id"] = "dragonkin"
    predator = replace(wolf, kind="dragonkin", identity=replace(wolf.identity, properties=props),
                       biological=replace(wolf.biological, hunger=HUNT_HUNGER + 40.0), combat=replace(wolf.combat, readiness=100.0),
                       navigation=replace(wolf.navigation, position=(20.0, 20.0), last_moved_tick=None, lodged_in=None))
    prey = replace(human, navigation=replace(human.navigation, position=(20.0 + dx, 20.0), last_moved_tick=None, lodged_in=None), combat=replace(human.combat, alive=True))
    state = replace(world, entities={**world.entities, predator.id: predator, prey.id: prey}, world_time=world_time, tick=world.tick + 1)
    return state, state.entities[predator.id], state.entities[prey.id]


# --- P1-1 -------------------------------------------------------------------------------------------------------------------------------------------

def test_night_and_tick_are_required_keyword_arguments_of_the_signal_chain():
    for fn in (relation, perceived_hostile, attack_allowed, perceives):
        params = inspect.signature(fn).parameters
        for name in ("night", "tick"):
            assert params[name].kind is inspect.Parameter.KEYWORD_ONLY and params[name].default is inspect.Parameter.empty, f"{fn.__name__}.{name} must be required keyword-only"


@pytest.mark.parametrize("fn,args", [(relation, 2), (perceived_hostile, 2), (perceives, 2), (attack_allowed, 3)])
def test_a_forgotten_night_or_tick_fails_at_the_call(world, fn, args):
    _, a, b = _pair(world, DAY_WORLD_TIME)
    call = (a, b) if args == 2 else (a, b, False)
    with pytest.raises(TypeError):
        fn(*call)
    with pytest.raises(TypeError):
        fn(*call, night=False)
    with pytest.raises(TypeError):
        fn(*call, tick=0)


@pytest.mark.parametrize("world_time", [DAY_WORLD_TIME, NIGHT_WORLD_TIME])
def test_the_decision_and_the_legality_agree_on_the_same_target_by_day_and_by_night(world, world_time):
    """By day the hunt is allowed and by night it is refused, and the decision's `perceived_hostile` says the same as the legality's verdict."""
    state, hunter, prey = _pair(world, world_time, dx=NIGHT_DX if world_time == NIGHT_WORLD_TIME else 2.0)
    night = is_night(state.world_time)
    decided = perceived_hostile(hunter, prey, night=night, tick=state.tick)
    legal, reason = LegalityServiceV2.verify_attack_legality(hunter, prey, state)
    refused_on_the_relation = (not legal) and reason is ReasonCode.FRIENDLY_FIRE_ILLEGAL
    assert decided is (not night)
    assert refused_on_the_relation is night, f"the legality must refuse exactly when the decision does not see a target; got {legal} {reason}"
    assert decided is not refused_on_the_relation


def test_a_context_with_no_clock_must_be_given_night_and_is_never_read_as_day(world):
    state, hunter, prey = _pair(world, NIGHT_WORLD_TIME, dx=NIGHT_DX)

    class NoClock:  # a context that carries entities and a tick but no world_time
        tick = state.tick
        entities = state.entities
        regions = state.regions
        terrain = state.terrain

    with pytest.raises(TypeError, match="world_time"):
        LegalityServiceV2.verify_attack_legality(hunter, prey, NoClock())
    legal, reason = LegalityServiceV2.verify_attack_legality(hunter, prey, state, night=True)
    assert reason is ReasonCode.FRIENDLY_FIRE_ILLEGAL


def test_a_night_kill_of_a_target_the_killer_cannot_perceive_is_not_a_feeding_kill(world):
    state, hunter, prey = _pair(world, NIGHT_WORLD_TIME, dx=NIGHT_DX)
    assert is_feeding_kill(state, hunter.id, prey) is False


def test_the_same_pair_by_day_is_a_feeding_kill(world):
    state, hunter, prey = _pair(world, DAY_WORLD_TIME)
    assert relation(hunter, prey, night=False, tick=state.tick) is Relation.PREDATION
    assert is_feeding_kill(state, hunter.id, prey) is True


# --- P1-2 -------------------------------------------------------------------------------------------------------------------------------------------

def _held(world, *, target_lodged=False, pursuer_lodged=False, world_time=NIGHT_WORLD_TIME):
    state, a, b = _pair(world, world_time, dx=1.0)  # adjacent: touch reaches it at any hour
    b = replace(b, navigation=replace(b.navigation, lodged_in="inn" if target_lodged else None))
    a = replace(a, navigation=replace(a.navigation, lodged_in="inn" if pursuer_lodged else None))
    state = replace(state, entities={**state.entities, a.id: a, b.id: b})
    return state, a, b


def test_an_unlodged_adjacent_held_target_is_still_perceived_by_touch_at_night(world):
    state, a, b = _held(world)
    assert _held_target_in_view(state, a, b.id) is True


def test_a_lodged_adjacent_held_target_is_not_perceived_and_the_pursuit_drops_it(world):
    state, a, b = _held(world, target_lodged=True)
    assert _held_target_in_view(state, a, b.id) is False


def test_a_lodged_pursuer_drops_an_adjacent_outside_target(world):
    state, a, b = _held(world, pursuer_lodged=True)
    assert _held_target_in_view(state, a, b.id) is False


def test_a_dead_held_target_is_dropped(world):
    state, a, b = _held(world)
    b = replace(b, combat=replace(b.combat, alive=False))
    assert _held_target_in_view(replace(state, entities={**state.entities, b.id: b}), a, b.id) is False


# --- the action-routing phase hands legality a clocked state (designer confirmation C1) ----------------------------------------------------------------

def _routed_reasons(world, world_time, dx=2.0):
    """Drive an ATTACK intent of the hunter on the prey through ActionRoutingPhase.route (-> SimulationDomainLogic.execute_action(context=sliding_state) -> CombatActions -> verify_attack_legality)."""
    from src.core.updates import EntityUpdate, StateUpdate, TaskUpdate
    from src.engine.pipeline_phases.actions import ActionRoutingPhase

    state, hunter, prey = _pair(world, world_time, dx=dx)
    update = StateUpdate(entity_updates={hunter.id: EntityUpdate(
        entity_id=hunter.id, task=TaskUpdate(work_kind_set="ENTITY_ACT", payload_set={"action": "ATTACK", "target_id": prey.id}))})
    refined = ActionRoutingPhase.route(state, update)
    return {getattr(ev.reason, "value", str(ev.reason)) for ev in refined.rejection_events if ev.actor_id == hunter.id}


def test_an_attack_intent_routed_through_the_action_phase_is_judged_by_the_states_clock(world):
    """The routed context is a clocked AuthoritativeState (a clockless one would raise): the same attack is refused on the relation at night and passes that step by day."""
    assert ReasonCode.FRIENDLY_FIRE_ILLEGAL.value in _routed_reasons(world, NIGHT_WORLD_TIME, dx=NIGHT_DX)
    assert ReasonCode.FRIENDLY_FIRE_ILLEGAL.value not in _routed_reasons(world, DAY_WORLD_TIME)


# --- PERC 3a changed expectations (divergence 2.229, AC2; WITH THE OWNER): at two tiles a still medium body IS seen at night, so the pair sees each other and only the range stops the strike ------------------

def test_at_two_tiles_by_night_the_decision_and_the_legality_both_see_the_pair(world):
    state, hunter, prey = _pair(world, NIGHT_WORLD_TIME, dx=2.0)
    assert perceived_hostile(hunter, prey, night=True, tick=state.tick) is True
    legal, reason = LegalityServiceV2.verify_attack_legality(hunter, prey, state)
    assert reason is not ReasonCode.FRIENDLY_FIRE_ILLEGAL and reason is ReasonCode.OUT_OF_RANGE  # seen, so refused only for range


def test_at_two_tiles_by_night_a_context_given_night_reaches_out_of_range_not_the_relation_refusal(world):
    state, hunter, prey = _pair(world, NIGHT_WORLD_TIME, dx=2.0)
    legal, reason = LegalityServiceV2.verify_attack_legality(hunter, prey, state, night=True)
    assert reason is ReasonCode.OUT_OF_RANGE


def test_a_night_kill_of_a_target_seen_at_two_tiles_is_a_feeding_kill(world):
    state, hunter, prey = _pair(world, NIGHT_WORLD_TIME, dx=2.0)
    assert is_feeding_kill(state, hunter.id, prey) is True


def test_an_attack_routed_at_two_tiles_by_night_is_refused_for_range_only(world):
    reasons = _routed_reasons(world, NIGHT_WORLD_TIME, dx=2.0)
    assert ReasonCode.FRIENDLY_FIRE_ILLEGAL.value not in reasons and ReasonCode.OUT_OF_RANGE.value in reasons
