"""SURV-07 LAW P grid, HUNT rows (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED; designer's defect read on 039c148a8, ruling: the gate does not stop a fight with
hostile h when HUNGER is pressing and relation(subject, h) is Relation.PREDATION, the predicate `opening_steps._hunt_step` uses).

Entities come from the compiled `frontier_living_world` (a wolf and a person are both hunters of `small_plant_eater`; a goblin is a faction-hostile non-prey for a person).
The prey is a hostile in sight and not acting. Rows state what the RULING requires; a row that fails on 039c148a8 is the defect, not a changed expectation."""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.strategic import ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine.appraisal import Relation
from src.engine.hostility import relation
from src.engine.tactical import TacticalDecisionSystem
from tests.helpers.scenario import compile_world

PRESSING_HUNGER, CALM_HUNGER, PRESSING_DEBT = 90.0, 20.0, 95.0


@pytest.fixture(scope="module")
def world():
    return compile_world("frontier_living_world", 42)


def _species(world, species):
    return next(e for e in world.entities.values() if (e.identity.properties or {}).get("species_id") == species)


def _at(entity, x, y):
    return replace(entity, navigation=replace(entity.navigation, position=(x, y)))


def _with_project(subject, project_kind, objective_kind, prey):
    obj = ObjectiveState(id="obj_hunt", kind=objective_kind, target=str(prey.id), target_entity_id=prey.id, status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id="proj_hunt", kind=project_kind, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    return replace(subject, strategic=replace(subject.strategic, projects={proj.id: proj}, current_project_id=proj.id, current_objective_id=obj.id))


def _decide(world, hunter_species, *, prey_dx, project=("hunger", ObjectiveKind.REACH_LOCATION), hunger=PRESSING_HUNGER, debt=0.0, extra=()):
    """The hunter at (30, 30), the prey `prey_dx` tiles east; `extra` is [(species, dx, dy)] of other entities."""
    base = _species(world, hunter_species)
    herd = _species(world, "small_plant_eater")
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=hunger, sleep_debt=debt))
    prey = _at(herd, 30.0 + prey_dx, 30.0)
    assert relation(hunter, prey) is Relation.PREDATION or hunger < 50.0, "the fixture must make the herd the hunter's prey"
    if project is not None:
        hunter = _with_project(hunter, project[0], project[1], prey)
    ents = {hunter.id: hunter, prey.id: prey}
    for sp, dx, dy in extra:
        e = next(x for x in world.entities.values() if (x.identity.properties or {}).get("species_id") == sp and x.id not in ents)
        ents[e.id] = _at(e, 30.0 + dx, 30.0 + dy)
    state = replace(world, entities=ents, tick=world.tick + 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hunter)
    return (update.task.payload_set if update.task is not None else None) or {}, update, hunter, prey, ents


HUNTERS = ["wolf", "human"]


@pytest.mark.parametrize("sp", HUNTERS)
def test_hunger_project_on_prey_walks_to_it_at_three_tiles(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=3.0)
    assert update.navigation is not None and update.navigation.target_set is not None, f"must walk toward the prey; got {payload}"


@pytest.mark.parametrize("sp", HUNTERS)
def test_hunger_project_on_prey_strikes_it_at_one_tile(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=1.0)
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == prey.id, f"got {payload}"


@pytest.mark.parametrize("sp", HUNTERS)
def test_combat_engage_project_on_prey_by_a_hungry_hunter_strikes_it_at_one_tile(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=1.0, project=("combat", ObjectiveKind.DEFEAT_ENEMY))
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == prey.id, f"got {payload}"


@pytest.mark.parametrize("sp", HUNTERS)
def test_pressing_hunger_with_no_project_and_prey_adjacent_strikes_it(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=1.0, project=None)
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == prey.id, f"got {payload}"


def test_pressing_sleep_only_with_prey_in_view_does_not_engage_it(world):
    """Hunger below the onset (so prey is not a hunger matter), sleep debt pressing: no exemption, the wait stands."""
    payload, update, hunter, prey, _ = _decide(world, "human", prey_dx=1.0, project=None, hunger=CALM_HUNGER, debt=PRESSING_DEBT)
    assert payload.get("action") != "ATTACK", f"got {payload}"


def test_prey_and_a_non_prey_hostile_both_in_view_engages_the_prey_only(world):
    payload, update, hunter, prey, ents = _decide(world, "human", prey_dx=1.0, extra=[("goblin", 0.0, 1.0)])
    goblin_ids = {i for i, e in ents.items() if (e.identity.properties or {}).get("species_id") == "goblin"}
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == prey.id and payload.get("target_id") not in goblin_ids, f"got {payload}"


def test_a_non_prey_non_acting_hostile_alone_is_not_engaged_by_a_pressing_hunter(world):
    base = _species(world, "human")
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=PRESSING_HUNGER, sleep_debt=0.0))
    gob = _at(_species(world, "goblin"), 31.0, 30.0)
    assert relation(hunter, gob) is not Relation.PREDATION
    state = replace(world, entities={hunter.id: hunter, gob.id: gob}, tick=world.tick + 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hunter)
    payload = (update.task.payload_set if update.task is not None else None) or {}
    assert payload.get("action") != "ATTACK", f"got {payload}"


# ---- the guard: an active need project whose objective names no living target keeps its walk; the exemption does not apply ---------------------------------

def _decide_with_way(world, project_kind, target, *, hunger=PRESSING_HUNGER, prey_dx=1.0, extra_prey_acting=False):
    base = _species(world, "human")
    herd = _species(world, "small_plant_eater")
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=hunger, sleep_debt=0.0))
    prey = _at(herd, 30.0 + prey_dx, 30.0)
    obj = ObjectiveState(id="obj_way", kind=ObjectiveKind.REACH_LOCATION, target=str(target), status=ObjectiveStatus.ACTIVE)
    proj = ProjectState(id="proj_way", kind=project_kind, status=ProjectStatus.ACTIVE, objectives=[obj], active_objective_id=obj.id)
    hunter = replace(hunter, strategic=replace(hunter.strategic, projects={proj.id: proj}, current_project_id=proj.id, current_objective_id=obj.id))
    state = replace(world, entities={hunter.id: hunter, prey.id: prey}, tick=world.tick + 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hunter)
    return (update.task.payload_set if update.task is not None else None) or {}, update


def _an_inn(world):
    return next(b for b in world.buildings.values() if b.kind == "inn")


def test_hunger_project_on_an_inn_stays_on_its_walk_with_prey_adjacent(world):
    inn = _an_inn(world)
    payload, update = _decide_with_way(world, "hunger", inn.id)
    assert payload.get("action") != "ATTACK" and update.navigation is not None and update.navigation.target_set is not None, f"got {payload}"


def test_fatigue_project_with_hunger_pressing_stays_on_its_walk_with_prey_adjacent(world):
    inn = _an_inn(world)
    payload, update = _decide_with_way(world, "fatigue", inn.id)
    assert payload.get("action") != "ATTACK" and update.navigation is not None and update.navigation.target_set is not None, f"got {payload}"


def test_hunger_project_on_a_carcass_stays_on_its_way_with_prey_adjacent(world):
    payload, update = _decide_with_way(world, "hunger", 99999)     # an objective naming a carcass id: no living target
    assert payload.get("action") != "ATTACK", f"got {payload}"


def test_a_hostile_acting_on_a_hungry_hunter_takes_the_normal_path_unchanged(world):
    """Hunger pressing with a hostile ACTING on the subject: `need_yields` is true, so the exemption never applies and the threat is fought as before."""
    from src.core.state import TaskComponent
    base = _species(world, "human")
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=PRESSING_HUNGER, sleep_debt=0.0))
    gob = _at(_species(world, "goblin"), 31.0, 30.0)
    gob = replace(gob, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": hunter.id}))
    state = replace(world, entities={hunter.id: hunter, gob.id: gob}, tick=world.tick + 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hunter)
    payload = (update.task.payload_set if update.task is not None else None) or {}
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == gob.id, f"got {payload}"


# ---- the hunt project is not suspended by its own prey, and it ends with its target (designer's condition on the exemption) ------------------------------------

def _suspends(update):
    return update.strategic is not None and bool(update.strategic.projects_add_or_update) and any(
        getattr(p.status, "value", p.status) == "SUSPENDED" for p in update.strategic.projects_add_or_update)


@pytest.mark.parametrize("sp", HUNTERS)
def test_the_hunt_project_stays_current_and_active_with_its_prey_in_view(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=1.0)
    assert not _suspends(update), "the hunter's own hunt project must not be suspended by its prey"
    assert update.strategic is None or update.strategic.current_project_id_set != ""


@pytest.mark.parametrize("sp", HUNTERS)
def test_a_combat_engage_project_on_prey_keeps_todays_suspension(world, sp):
    payload, update, hunter, prey, _ = _decide(world, sp, prey_dx=1.0, project=("combat", ObjectiveKind.DEFEAT_ENEMY))
    assert _suspends(update), "COMBAT_ENGAGE is not a need project: today's suspension stays"


def test_a_hunt_project_naming_x_with_prey_y_also_in_view_stays_current_and_the_hunter_may_take_y(world):
    base = _species(world, "human")
    herd = [e for e in world.entities.values() if (e.identity.properties or {}).get("species_id") == "small_plant_eater"][:2]
    x, y = _at(herd[0], 33.0, 30.0), _at(herd[1], 31.0, 30.0)
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=PRESSING_HUNGER, sleep_debt=0.0))
    hunter = _with_project(hunter, "hunger", ObjectiveKind.REACH_LOCATION, x)
    state = replace(world, entities={hunter.id: hunter, x.id: x, y.id: y}, tick=world.tick + 1)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hunter)
    payload = (update.task.payload_set if update.task is not None else None) or {}
    assert not _suspends(update)
    assert payload.get("action") == "ATTACK" and payload.get("target_id") == y.id, f"got {payload}"


def _hunter_with_hunt(world, prey_alive=True, prey_dx=1.0):
    base = _species(world, "human")
    herd = _species(world, "small_plant_eater")
    hunter = replace(_at(base, 30.0, 30.0), biological=replace(base.biological, hunger=PRESSING_HUNGER, sleep_debt=0.0))
    prey = _at(herd, 30.0 + prey_dx, 30.0)
    if not prey_alive:
        prey = replace(prey, combat=replace(prey.combat, alive=False, hp=0))
    hunter = _with_project(hunter, "hunger", ObjectiveKind.REACH_LOCATION, prey)
    return replace(world, entities={hunter.id: hunter, prey.id: prey}, tick=world.tick + 1), hunter, prey


def test_the_hunt_objective_ends_with_its_target_dead_gone_or_out_of_perception(world):
    """Pins `_hunt_step`'s docstring ("the objective ends with its target") against the lifecycle predicate the evaluator and the work queue share."""
    from src.core.combat_constants import ENTITY_TARGET_PERCEPTION_RADIUS
    from src.core.strategic import ObjectiveStatus, ProjectStatus
    from src.systems.strategic_systems.entity_target_objective import objective_outcome
    for kwargs, expected in (({"prey_alive": False}, (ObjectiveStatus.RESOLVED, ProjectStatus.COMPLETED)),
                             ({"prey_dx": ENTITY_TARGET_PERCEPTION_RADIUS + 5.0}, (ObjectiveStatus.FAILED, ProjectStatus.ABANDONED))):
        state, hunter, prey = _hunter_with_hunt(world, **kwargs)
        project = hunter.strategic.projects[hunter.strategic.current_project_id]
        out = objective_outcome(hunter, state, project, project.objectives[0])
        assert out is not None and (out.objective, out.project) == expected, kwargs
    state, hunter, prey = _hunter_with_hunt(world)
    project = hunter.strategic.projects[hunter.strategic.current_project_id]
    assert objective_outcome(hunter, state, project, project.objectives[0]) is None     # alive and in view: it holds
    gone = replace(state, entities={hunter.id: hunter})
    out = objective_outcome(hunter, gone, project, project.objectives[0])
    assert out is not None and out.project == ProjectStatus.ABANDONED


def test_the_evaluator_clears_the_current_project_when_the_prey_dies(world):
    from src.core.strategic import ProjectStatus
    from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem
    state, hunter, prey = _hunter_with_hunt(world, prey_alive=False)
    up = StrategicIntelligenceSystem.evaluate_strategic_intent(state, hunter, force=True)
    assert up.current_project_id_set == "" and up.current_objective_id_set == "", "no stuck current project"
    assert up.projects_add_or_update and up.projects_add_or_update[0].status == ProjectStatus.COMPLETED, "no orphan: the project is COMPLETED"
