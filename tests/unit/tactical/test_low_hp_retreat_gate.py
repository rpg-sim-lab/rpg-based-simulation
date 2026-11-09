"""The low-hp pure retreat (tactical.py, hp under 15%) and the precedence grid rows of this site (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE).

Site 4 of the SURV-07 law P grid: {need pressing y/n} x {no hostile / perceived only / present, not acting / acting} -> winner. A pressing need runs first (`need_first`) unless a hostile acts on
the subject; a retreat with no destination is not taken (no no-op PANIC_RETREAT, no RETREAT mode over the subject's own tile). The emotional panic branch ahead of it is switched off in these
rows (`_panic_holds` False) so only this site is under test; the panic branch is the ticket's scope 2(c).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

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


def _stamps_a_move(update):
    return update.navigation is not None and (update.navigation.target_set is not None or update.navigation.movement_mode_set is not None)


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
def test_a_retreat_with_nowhere_to_go_stamps_no_move(monkeypatch, hunger, hostile_at, task, label, wins):
    """No destination: no no-op PANIC_RETREAT and no RETREAT mode over the subject's own tile. A pressing need still eats (it ran first); a hostile acting does not make it fight."""
    update = _decide(monkeypatch, hunger, hostile_at, task, destination="none")
    payload = _payload(update)
    assert payload.get("reason") != "PANIC_RETREAT", f"got {payload}"
    if hunger == PRESSING_HUNGER and task is None:
        assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"
    else:
        assert not _stamps_a_move(update) and payload.get("action") != "ATTACK", f"got {update}"


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
