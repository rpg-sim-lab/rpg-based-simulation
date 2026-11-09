"""The low-hp pure retreat (tactical.py, hp under 15%) and the precedence grid rows of this site (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE).

Site 4 of the SURV-07 law P grid: {need pressing y/n} x {no hostile / perceived only / present, not acting / acting} -> winner. A pressing need runs first (`need_first`) unless a hostile acts on
the subject; a retreat with no destination is not taken (no no-op PANIC_RETREAT, no RETREAT mode over the subject's own tile). The emotional panic branch ahead of it is switched off in these
rows (`_panic_holds` False) so only this site is under test; the panic branch is the ticket's scope 2(c).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.movement_modes import MovementMode
from src.engine import tactical as tactical_module
from src.engine.tactical import TacticalDecisionSystem
from tests.unit.tactical.test_surv07_precedence_grid import ATTACKS_THE_HERO, CALM_HUNGER, INN_ID, PRESSING_HUNGER, _hungry_hero

HP = 8  # of 85: under 15%


def _decide(monkeypatch, hunger, hostile_at, hostile_task, destination="none"):
    monkeypatch.setattr(tactical_module, "_panic_holds", lambda *a, **k: False)
    if destination != "none":
        monkeypatch.setattr(tactical_module, "retreat_destination", lambda *a, **k: destination)
    else:
        monkeypatch.setattr(tactical_module, "retreat_destination", lambda *a, **k: None)
    state, hero = _hungry_hero(hunger, hostile_at=hostile_at, hostile_task=hostile_task)
    hero = replace(hero, combat=replace(hero.combat, hp=HP))
    state = replace(state, entities={**state.entities, 1: hero})
    return TacticalDecisionSystem.evaluate_entity_intent(state, hero)


def _payload(update):
    return (update.task.payload_set if update.task is not None else None) or {}


NO_HOSTILE, PERCEIVED, ADJACENT = None, (39.0, 26.0), (39.0, 30.0)

ROWS = [
    # (hunger, hostile at, hostile task, label, wins)
    (PRESSING_HUNGER, NO_HOSTILE, None, "pressing, no hostile", "need"),
    (PRESSING_HUNGER, PERCEIVED, None, "pressing, hostile perceived only", "need"),
    (PRESSING_HUNGER, ADJACENT, None, "pressing, hostile adjacent but not acting", "need"),
    (PRESSING_HUNGER, ADJACENT, ATTACKS_THE_HERO, "pressing, hostile acting", "threat"),
    (CALM_HUNGER, NO_HOSTILE, None, "calm, no hostile", "need"),
    (CALM_HUNGER, PERCEIVED, None, "calm, hostile perceived only", "threat"),
    (CALM_HUNGER, ADJACENT, None, "calm, hostile adjacent but not acting", "threat"),
    (CALM_HUNGER, ADJACENT, ATTACKS_THE_HERO, "calm, hostile acting", "threat"),
]


@pytest.mark.parametrize("hunger,hostile_at,task,label,wins", ROWS, ids=[r[3] for r in ROWS])
def test_the_low_hp_retreat_rows_with_a_destination(monkeypatch, hunger, hostile_at, task, label, wins):
    """With somewhere to go: the need wins unless a hostile acts, and any other hostile in view is fled from, as before."""
    update = _decide(monkeypatch, hunger, hostile_at, task, destination=(30.0, 31.0))
    payload = _payload(update)
    if wins == "need":
        assert payload.get("reason") != "PANIC_RETREAT" and (hostile_at is None or payload.get("action") == "EAT"), f"got {payload}"
    else:
        assert payload.get("reason") == "PANIC_RETREAT" and tuple(payload["target_position"]) == (30.0, 31.0), f"got {payload}"


@pytest.mark.parametrize("hunger,hostile_at,task,label,wins", [r for r in ROWS if r[1] is not None], ids=[r[3] for r in ROWS if r[1] is not None])
def test_a_retreat_with_nowhere_to_go_holds_without_a_panic_task(monkeypatch, hunger, hostile_at, task, label, wins):
    """No destination: no PANIC_RETREAT task and no ATTACK. A pressing need still eats (it ran first); any other row holds its own tile in RETREAT mode with no task (rpg-designer: the
    hold stays, so a stored target elsewhere is not walked)."""
    update = _decide(monkeypatch, hunger, hostile_at, task, destination="none")
    payload = _payload(update)
    assert payload.get("reason") != "PANIC_RETREAT" and payload.get("action") in (None, "EAT"), f"got {payload}"
    if hunger == PRESSING_HUNGER and task is None:
        assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"
    else:
        assert update.task is None and update.navigation is not None, f"got {update}"
        assert update.navigation.movement_mode_set is MovementMode.RETREAT and tuple(update.navigation.target_set) == (39.0, 31.0), f"got {update.navigation}"


def test_the_acceptance_scene_a_low_hp_subject_beside_a_non_acting_hostile_steps_to_the_inn_and_eats(monkeypatch):
    """The ticket's AC with the emotional panic branch out of the way: hp 8 of 85, a hostile beside it that does not act, the hunger project's inn one tile off. Its intent is the meal,
    not a no-op PANIC_RETREAT. (Below the consequence line the panic branch itself still holds first: scope 2(c).)"""
    update = _decide(monkeypatch, PRESSING_HUNGER, ADJACENT, None)
    payload = _payload(update)
    assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID and payload.get("reason") != "PANIC_RETREAT", f"got {payload}"


# ---- scope 2(c): the emotional panic freeze with no destination, below the consequence line ---------------------------------------------------------------

def _prey_scene(monkeypatch, hunger=80.0, hp=8, prey_dx=1.0):
    """A person at hp 8/85 with a hunger project, a small plant-eater (prey) beside it, and no destination for any retreat."""
    from src.engine.appraisal import Relation
    from src.engine.hostility import relation
    from tests.helpers.scenario import compile_world
    from tests.unit.tactical.test_surv07_hunt_project_grid import _at, _species, _with_project
    from src.core.strategic import ObjectiveKind

    monkeypatch.setattr(tactical_module, "retreat_destination", lambda *a, **k: None)
    # The appraisal does not count a plant-eater as a threat to a person, so the panic would never start; stage the prey as a perceived threat as well (the case the guard is for).
    monkeypatch.setattr(tactical_module, "perceived_threats", lambda entity, neighbors: [n for n in neighbors if n.combat.alive])
    world = compile_world("frontier_living_world", 42)
    base, herd = _species(world, "human"), _species(world, "small_plant_eater")
    person = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=hunger, sleep_debt=0.0),
                     combat=replace(base.combat, hp=hp, max_hp=85))
    prey = _at(herd, 30.0 + prey_dx, 30.0)
    assert relation(person, prey) is Relation.PREDATION, "the fixture must make the herd the person's prey"
    person = _with_project(person, "hunger", ObjectiveKind.REACH_LOCATION, prey)
    state = replace(world, entities={person.id: person, prey.id: prey}, tick=world.tick + 1)
    return TacticalDecisionSystem.evaluate_entity_intent(state, person), person


def test_a_panic_freeze_with_prey_in_sight_holds_and_does_not_attack_the_prey(monkeypatch):
    """The guard on the yield: with prey in sight `need_first` is False (the hunt exemption), so a yielded freeze would fall through to engagement and an hp 8/85 subject would attack a
    non-acting prey animal. The freeze holds: PANIC_RETREAT on its own tile, not ATTACK."""
    update, person = _prey_scene(monkeypatch)
    payload = _payload(update)
    assert payload.get("reason") == "PANIC_RETREAT" and tuple(payload["target_position"]) == person.navigation.position, f"got {payload}"
    assert payload.get("action") != "ATTACK"


def _panic_scene(monkeypatch, destination, hostile_task=None):
    """The reading-3 scene with the panic branch LIVE (`_panic_holds` untouched): hp 8/85, hunger 80 (pressing, below the line), a hostile beside it."""
    monkeypatch.setattr(tactical_module, "retreat_destination", lambda *a, **k: destination)
    state, hero = _hungry_hero(PRESSING_HUNGER, hostile_at=ADJACENT, hostile_task=hostile_task)
    hero = replace(hero, combat=replace(hero.combat, hp=HP))
    state = replace(state, entities={**state.entities, 1: hero})
    return TacticalDecisionSystem.evaluate_entity_intent(state, hero), hero


def test_a_panic_with_a_destination_still_flees_against_a_pressing_need(monkeypatch):
    """Row 88 (5): the yield is only for the no-destination case. Same scene as reading 3 below the line, but the panic has somewhere to go: PANIC_RETREAT to it."""
    update, _ = _panic_scene(monkeypatch, destination=(30.0, 31.0))
    payload = _payload(update)
    assert payload.get("reason") == "PANIC_RETREAT" and tuple(payload["target_position"]) == (30.0, 31.0), f"got {payload}"


def test_an_acting_hostile_with_no_destination_keeps_the_freeze(monkeypatch):
    """The yield needs nothing acting on the subject: a hostile attacking it keeps the freeze on its own tile, not the meal."""
    update, hero = _panic_scene(monkeypatch, destination=None, hostile_task=ATTACKS_THE_HERO)
    payload = _payload(update)
    assert payload.get("reason") == "PANIC_RETREAT" and tuple(payload["target_position"]) == hero.navigation.position and payload.get("action") != "EAT", f"got {payload}"


def test_a_held_retreat_does_not_walk_a_stored_target_through_the_kernel(monkeypatch):
    """Rpg-designer's pin: hp under 15%, an acting hostile adjacent, no destination, and a stored target elsewhere. The hold (own tile, RETREAT mode, no task) is inert: through the
    kernel's first decisions (this subject decides at ticks 9 and 13) its position is unchanged and it holds no PANIC_RETREAT task. An idle update instead lets the stored target walk it
    from tick 14 (checked). The emotional panic branch is switched off so the low-hp branch is the one under test. The brain decides on a cadence, so the row runs 16 ticks and asserts
    the low-hp branch really ran (the decisions are counted), not a single tick that decides nothing."""
    from tests.unit.engine.lodging_kernel import hero, kernel
    from src.core.builder import V2EntityBuilder
    from src.core.enums import Faction
    from src.core.state import TaskComponent

    monkeypatch.setattr(tactical_module, "_panic_holds", lambda *a, **k: False)
    monkeypatch.setattr(tactical_module, "retreat_destination", lambda *a, **k: None)
    decisions = []
    real = TacticalDecisionSystem.evaluate_entity_intent

    def spy(state, entity, *a, **kw):
        update = real(state, entity, *a, **kw)
        if entity.id == 1:
            decisions.append(update)
        return update

    monkeypatch.setattr(TacticalDecisionSystem, "evaluate_entity_intent", staticmethod(spy))
    me = hero(1, (15.0, 15.0), debt=0.0, gold=0, action=None, project=False)
    me = replace(me, combat=replace(me.combat, hp=8, max_hp=100, def_stat=50),
                 navigation=replace(me.navigation, movement_mode=MovementMode.WANDER, target=(25.0, 25.0)))
    foe = (V2EntityBuilder(2).kind("MONSTER").location(15.0, 16.0).identity(faction=Faction.MONSTER_HORDE)
           .combat(hp=300, max_hp=300, atk=1, def_stat=5, alive=True, readiness=100.0).navigation(movement_mode=MovementMode.WANDER).lifecycle(active=True).build())
    foe = replace(foe, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1}))
    k = kernel([me, foe])
    try:
        for _ in range(16):
            k.tick_once()
            assert k._state.entities[1].navigation.position == (15.0, 15.0), f"walked to {k._state.entities[1].navigation.position} at tick {k._state.tick}"
            assert (k._state.entities[1].task.payload or {}).get("reason") != "PANIC_RETREAT"
    finally:
        k.shutdown()
    assert len(decisions) >= 2 and all(d.task is None and d.navigation.movement_mode_set is MovementMode.RETREAT for d in decisions), "the low-hp hold must have been decided"
