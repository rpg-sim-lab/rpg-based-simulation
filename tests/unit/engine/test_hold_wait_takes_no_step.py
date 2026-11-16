"""A typed wait takes no step on its own tick and none in the gap before the next decision (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, P1-b and P2).

The movement phase reads the tick-START entity, so a wait decided this tick used to walk the target stored before it (an opportunity attack
per step). The waits (WATCH_HOSTILE, AVOID_NO_ROUTE, HOLD_CHOKEPOINT) now clear the stored target in the same update that sets HOLD, and
``MovementCandidateSelector.movement_target`` returns no target for a pending update that clears the target and sets none. P1-b depends on P2:
the first test pins both halves.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, RegionState, TaskComponent
from src.core.updates import EntityUpdate, NavigationUpdate, TaskUpdate
from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
from src.engine.candidate_selector import MovementCandidateSelector as MCS
from src.engine.tactical_hold import held_swing_update, notice_unengaged_hostile

GOAL = (40.0, 40.0)


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def _fighter(eid, pos, faction):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (V2EntityBuilder(eid).kind("hero" if role == EntityRole.HERO else "monster").location(*pos)
            .identity(role=role, faction=faction).combat(hp=100, max_hp=100, attack_range=1, readiness=100.0, alive=True)
            .lifecycle(active=True).build())


def _walker(posture):
    e = _fighter(1, (10.0, 10.0), Faction.HERO_GUILD)
    props = dict(e.identity.properties)
    props["last_combat_posture"], props["last_combat_posture_target"] = posture, 2
    return replace(e, navigation=replace(e.navigation, target=GOAL, movement_mode=MovementMode.WANDER),
                   identity=replace(e.identity, properties=props), task=TaskComponent(work_kind="ENTITY_ACT", payload={}))


def _hostile():
    return replace(_fighter(2, (10.0, 11.0), Faction.MONSTER_HORDE), task=TaskComponent(work_kind="ENTITY_ACT", payload={}))


def _state(w, h):
    return AuthoritativeState(tick=5, seed=1, entities={1: w, 2: h}, regions={"field": RegionState(id="field", name="Field", bounds=(0, 0, 60, 60))})


def _wait_update(kind, monkeypatch):
    """The decision of the walker beside the unengaged hostile for ``kind``, as the tactical pass emits it."""
    import src.engine.tactical_hold as tactical_hold

    posture = "watch" if kind == "WATCH_HOSTILE" else "avoid"
    if kind == "AVOID_NO_ROUTE":
        monkeypatch.setattr(tactical_hold, "retreat_destination", lambda *args, **kwargs: None)
    w, h = _walker(posture), _hostile()
    return w, h, notice_unengaged_hostile(_state(w, h), w, h, [h], None)


def _as_the_actions_phase_leaves_it(update):
    """The real order: action_routing runs before movement_routing and empties a successful HOLD's payload (pipeline_phases/actions.py)."""
    return replace(update, task=replace(update.task, payload_set={}))


@pytest.mark.parametrize("kind", ["WATCH_HOSTILE", "AVOID_NO_ROUTE"])
def test_p1b_depends_on_p2_a_wait_without_target_clear_still_walks_and_with_it_does_not(kind, monkeypatch):
    w, h, update = _wait_update(kind, monkeypatch)
    update = _as_the_actions_phase_leaves_it(update)
    assert update.navigation.movement_mode_set == MovementMode.HOLD and update.navigation.target_clear is True  # P2
    ents = {1: w, 2: h}
    assert MCS.movement_target(w, update, ents) is None  # P1-b: the update clears the stored target, nothing is left to walk
    without = replace(update, navigation=replace(update.navigation, target_clear=False))
    assert MCS.movement_target(w, without, ents) == GOAL  # P1-b alone does nothing: the walk happens (the entry-tick step)


def test_the_chokepoint_hold_clears_the_stored_target_too():
    from tests.unit.combat.test_chokepoint_hold import F, H, _staged
    from src.engine.tactical import TacticalDecisionSystem

    state = _staged()
    update = TacticalDecisionSystem.evaluate_entity_intent(state, state.entities[F], [state.entities[H]], 0.0)
    assert update.task.payload_set["reason"] == "HOLD_CHOKEPOINT"
    assert update.navigation.movement_mode_set == MovementMode.HOLD and update.navigation.target_clear is True


@pytest.mark.parametrize("kind", ["WATCH_HOSTILE", "AVOID_NO_ROUTE"])
def test_in_the_gap_after_the_wait_the_cleared_target_offers_no_move(kind, monkeypatch):
    w, h, update = _wait_update(kind, monkeypatch)
    after = replace(w, navigation=replace(w.navigation, target=None, movement_mode=MovementMode.HOLD))  # the wait applied
    assert MCS.movement_target(after, None, {1: after, 2: h}) is None


def test_a_decided_move_with_a_target_this_tick_still_moves_from_hold():
    w = replace(_walker("ignore"), navigation=replace(_walker("ignore").navigation, movement_mode=MovementMode.HOLD))
    decided = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=GOAL, movement_mode_set=MovementMode.WANDER),
                           task=TaskUpdate(work_kind_set="ENTITY_MOVE", payload_set={"target_position": GOAL, "reason": "KEEP_WALKING"}))
    assert MCS.movement_target(w, decided, {1: w, 2: _hostile()}) == GOAL


def test_an_attack_emission_takes_no_stored_step_on_its_own_tick():
    """The extra side effect of P1-b: an ATTACK / SKILL decision carries target_clear, so its tick no longer walks a stored target."""
    w = replace(_walker("engage"), combat=replace(_walker("engage").combat, readiness=50.0))
    h = replace(_hostile(), navigation=replace(_hostile().navigation, position=(10.0, 11.0)))
    held = held_swing_update(_state(w, h), w, h, None, {})
    assert held is not None and held.navigation.target_clear is True
    assert MCS.movement_target(w, held, {1: w, 2: h}) is None


def test_an_update_that_sets_a_target_and_clears_is_not_treated_as_a_clear():
    w = _walker("watch")
    both = EntityUpdate(entity_id=1, navigation=NavigationUpdate(target_set=(1.0, 1.0), target_clear=True))
    assert MCS.movement_target(w, both, {1: w, 2: _hostile()}) == (1.0, 1.0)


def test_a_hold_action_success_does_not_reset_the_mode_in_the_actions_phase():
    """The wait's task ends in its own tick; its HOLD stays until the next walk decision (it is not reset by the task end)."""
    from src.core.updates import StateUpdate
    from src.engine.pipeline_phases.actions import ActionRoutingPhase
    from src.engine.tactical import TacticalDecisionSystem
    from tests.unit.combat.test_chokepoint_hold import F, H, _staged

    state = _staged()
    decision = TacticalDecisionSystem.evaluate_entity_intent(state, state.entities[F], [state.entities[H]], 0.0)
    refined = ActionRoutingPhase.route(state, StateUpdate(entity_updates={F: decision}))
    held = refined.entity_updates[F]
    assert held.task.payload_set == {}  # the task ended in its own tick
    assert held.navigation.movement_mode_set == MovementMode.HOLD and held.navigation.target_clear is True
