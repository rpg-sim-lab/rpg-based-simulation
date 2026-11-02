"""SURV-07 LAW P precedence grid (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED).

At every site that weighs a need past its escalation onset against another goal or act, the need wins unless a hostile ACTS on the subject (`need_yields` =
`acting_threat_to`, memo row 88). One grid: {need pressing: yes / no} x {no hostile / perceived only / present, not acting / acting} x site -> winner.
Each "no" row asserts today's behaviour, each pressing and not-acting row asserts that the need wins, each acting row asserts that the threat wins.
Sites in this file: tactical.py presence skip (`if not hostiles:`, the hunger arrival); tactical_rest in-place rest; tactical_rest eat carried food.
Later tickets add their own rows (low-hp retreat, town return, escalated switch, flee line).
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.movement_modes import MovementMode
from src.core.state import AuthoritativeState, BuildingState, ItemStack, TaskComponent
from src.core.strategic import GoalKind, ObjectiveKind, ObjectiveState, ObjectiveStatus, ProjectState, ProjectStatus
from src.engine import tactical as tactical_module
from src.engine.need_pull import ESCALATION_ONSET, HUNGER_LINE, SLEEP_LINE
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_rest import eat_carried_update, rest_in_place_update

INN = (40.0, 31.0)
INN_ID = 20003
PRESSING_HUNGER, CALM_HUNGER = 80.0, 40.0
PRESSING_DEBT, CALM_DEBT = 90.0, 50.0


def test_the_fixture_values_sit_on_the_right_side_of_the_onset():
    assert PRESSING_HUNGER >= ESCALATION_ONSET * HUNGER_LINE > CALM_HUNGER
    assert PRESSING_DEBT >= ESCALATION_ONSET * SLEEP_LINE > CALM_DEBT


# ---- site 1: tactical.py presence skip (`if not hostiles:` gates the hunger arrival) -------------------------------------------------------------------------

def _hungry_hero(hunger, hostile_at=None, hostile_task=None, hero_at=(39.0, 31.0)):
    hero = (V2EntityBuilder(1).kind("HERO").location(*hero_at).identity(faction=Faction.HERO_GUILD)
            .combat(hp=85, max_hp=85, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=INN).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, hunger=hunger, sleep_debt=0.0))
    objective = ObjectiveState(id="hunger_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="proj_hunger_1", kind="hunger", status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id=objective.id)
    hero = replace(hero, strategic=replace(hero.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id=objective.id))
    entities = {1: hero}
    if hostile_at is not None:
        monster = (V2EntityBuilder(2).kind("MONSTER").location(*hostile_at).identity(faction=Faction.MONSTER_HORDE)
                   .combat(hp=300, max_hp=300, atk=60, def_stat=5, alive=True, readiness=100.0)
                   .navigation(movement_mode=MovementMode.WANDER).lifecycle(active=True).build())
        if hostile_task is not None:
            monster = replace(monster, task=hostile_task)
        entities[2] = monster
    inn = BuildingState(id=INN_ID, kind="inn", position=INN, functional=True)
    return AuthoritativeState(tick=1, seed=1, entities=entities, buildings={INN_ID: inn}, blocked_tiles={(40, 31)}, building_tiles={}, terrain={}), hero


ATTACKS_THE_HERO = TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1})
ROWS_266 = [
    # (hunger, hostile position, hostile task, label, the winner)
    (PRESSING_HUNGER, None, None, "pressing, no hostile", "need"),
    (PRESSING_HUNGER, (39.0, 26.0), None, "pressing, hostile perceived only", "need"),
    (PRESSING_HUNGER, (39.0, 30.0), None, "pressing, hostile adjacent but not acting", "need"),
    (PRESSING_HUNGER, (39.0, 30.0), ATTACKS_THE_HERO, "pressing, hostile acting", "threat"),
    (CALM_HUNGER, None, None, "calm, no hostile", "need"),
    (CALM_HUNGER, (39.0, 26.0), None, "calm, hostile perceived only", "not the need"),
    (CALM_HUNGER, (39.0, 30.0), None, "calm, hostile adjacent but not acting", "not the need"),
    (CALM_HUNGER, (39.0, 30.0), ATTACKS_THE_HERO, "calm, hostile acting", "threat"),
]


@pytest.mark.parametrize("hunger,hostile_at,hostile_task,label,winner", ROWS_266, ids=[r[3] for r in ROWS_266])
def test_the_presence_skip_row(monkeypatch, hunger, hostile_at, hostile_task, label, winner):
    seen = {"rest_called": 0, "pursue_called": 0, "hostiles": 0}
    real_rest, real_pursue, real_classify = tactical_module.in_place_survival_update, TacticalDecisionSystem._pursue_objective, tactical_module.classify_neighbours

    def spy_rest(*a, **k):
        seen["rest_called"] += 1
        return real_rest(*a, **k)

    def spy_classify(*a, **k):
        hood = real_classify(*a, **k)
        seen["hostiles"] = len(hood.hostiles)
        return hood

    def spy_pursue(*a, **k):
        seen["pursue_called"] += 1
        return real_pursue(*a, **k)

    monkeypatch.setattr(tactical_module, "in_place_survival_update", spy_rest)
    monkeypatch.setattr(tactical_module, "classify_neighbours", spy_classify)
    monkeypatch.setattr(TacticalDecisionSystem, "_pursue_objective", staticmethod(spy_pursue))
    state, hero = _hungry_hero(hunger, hostile_at, hostile_task)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    payload = (update.task.payload_set if update.task is not None else None) or {}

    # Which branch returned: past the panic branch (tactical.py ~:213) and the in-place survival step (~:262), i.e. the decision was made AT the presence skip.
    assert payload.get("reason") != "PANIC_RETREAT", "the row exited through the panic branch, so it does not test the presence skip"
    assert seen["rest_called"] == 1, "the decision did not reach the in-place survival step before the presence skip"
    assert seen["hostiles"] == (0 if hostile_at is None else 1)
    if winner == "need":
        assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, label
    elif winner == "threat":
        assert payload.get("action") == "ATTACK" and seen["pursue_called"] == 0, label
    else:  # today's behaviour below the onset: the presence skip still holds the hunger arrival back
        assert payload.get("action") != "EAT" and seen["pursue_called"] == 0, label


def test_a_pressing_follower_takes_no_part_in_the_groups_target_unless_it_is_acting_on_the_follower():
    """The gate sits before target selection and does not touch group_bias: the hostile is the group's SHARED target (leader 3 is fighting it), the follower is
    pressing and the hostile is not acting on it, so the follower walks to eat. Make the hostile act on the follower and the follower fights."""
    from src.core.state import GroupRecord

    for task, eats in ((None, True), (ATTACKS_THE_HERO, False)):
        state, hero = _hungry_hero(PRESSING_HUNGER, hostile_at=(39.0, 26.0), hostile_task=task)
        hero = replace(hero, identity=replace(hero.identity, group_id=7))
        leader = (V2EntityBuilder(3).kind("HERO").location(38.0, 26.0).identity(faction=Faction.HERO_GUILD)
                  .combat(hp=85, max_hp=85, atk=10, def_stat=5, alive=True, readiness=100.0).lifecycle(active=True).build())
        group = GroupRecord(id=7, leader_id=3, member_ids={1, 3}, anchor=(38.0, 26.0), shared_target_id=2)
        state = AuthoritativeState(tick=1, seed=1, entities={**state.entities, 1: hero, 3: leader}, buildings=state.buildings, blocked_tiles=state.blocked_tiles,
                                   building_tiles={}, terrain={}, groups={7: group})
        update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
        payload = update.task.payload_set or {}
        if eats:
            assert payload.get("action") == "EAT"
        else:  # the threat wins: the follower closes on the hostile that is acting on it (the group's target is the same body here)
            assert payload.get("action") != "EAT" and payload.get("target_id") == 2


# ---- site 2: tactical_rest rest in place -------------------------------------------------------------------------------------------------------------------

def _sleepy_hero(sleep_debt):
    hero = (V2EntityBuilder(1).kind("hero").location(0.0, 0.0).identity(faction=Faction.HERO_GUILD)
            .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, sleep_debt=sleep_debt))
    objective = ObjectiveState(id="o1", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="p1", kind=GoalKind.FATIGUE, status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id="o1")
    return replace(hero, strategic=replace(hero.strategic, projects={"p1": project}, current_project_id="p1", current_objective_id="o1"))


def _hostile(pos, task=None):
    m = (V2EntityBuilder(2).kind("monster").location(float(pos[0]), float(pos[1])).identity(faction=Faction.MONSTER_HORDE)
         .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    return replace(m, task=task) if task is not None else m


def _rest_state(hero, *others):
    return AuthoritativeState(tick=500, seed=1, entities={e.id: e for e in (hero, *others)}, buildings={INN_ID: BuildingState(id=INN_ID, kind="inn", position=(200.0, 0.0), functional=True)})


def _rests(update):
    return update is not None and (update.task.payload_set or {}).get("action") == "REST"


@pytest.fixture(scope="module", autouse=True)
def _consumers():
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    repo = CatalogRepository("data/content")
    repo.load_all()
    configure_behavior_consumers(repo)
    yield
    reset_behavior_consumers()


def test_rest_in_place_pressing_rows():
    hero = _sleepy_hero(PRESSING_DEBT)
    assert _rests(rest_in_place_update(_rest_state(hero), hero, []))                                                   # no hostile
    assert _rests(rest_in_place_update(_rest_state(hero, _hostile((12, 0))), hero, [_hostile((12, 0))]))               # perceived only
    assert _rests(rest_in_place_update(_rest_state(hero, _hostile((1, 0))), hero, [_hostile((1, 0))]))                 # adjacent, not acting: the need wins (changed)
    attacking = _hostile((1, 0), TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1}))
    assert rest_in_place_update(_rest_state(hero, attacking), hero, [attacking]) is None                              # acting by task: the threat wins


def test_rest_in_place_a_hit_inside_the_window_is_acting_and_an_old_hit_is_not():
    from src.engine.tactical_threat import NEED_WAKE_CADENCE

    hero = _sleepy_hero(PRESSING_DEBT)
    other = _hostile((1, 0))
    recent = replace(hero, combat=replace(hero.combat, last_attacker_id=2, last_hit_tick=500 - NEED_WAKE_CADENCE))
    assert rest_in_place_update(_rest_state(recent, other), recent, [other]) is None
    old = replace(hero, combat=replace(hero.combat, last_attacker_id=2, last_hit_tick=500 - NEED_WAKE_CADENCE - 1))
    assert _rests(rest_in_place_update(_rest_state(old, other), old, [other]))


def test_rest_in_place_a_hostile_targeting_by_payload_alone_is_not_acting():
    """The old test's targeting=1 row at distance 9: a bare target_id on a task that is neither an attack nor a pursuit is not an act (tactical_threat._task_acts_on)."""
    from src.ai.goals.present_threat import acting_threat_to

    hero = _sleepy_hero(PRESSING_DEBT)
    targeting = replace(_hostile((9, 0)), task=replace(_hostile((9, 0)).task, payload={"target_id": 1}))
    state = _rest_state(hero, targeting)
    assert not acting_threat_to(hero, state)
    assert _rests(rest_in_place_update(state, hero, [targeting]))     # lands on REST: the need wins


def test_rest_in_place_calm_rows_keep_the_agency_07_terms():
    """Below the onset nothing changed: an adjacent hostile, or one targeting by payload, still blocks the rest (the moved rows of test_rest_in_place.py)."""
    hero = _sleepy_hero(CALM_DEBT)
    assert rest_in_place_update(_rest_state(hero, _hostile((1, 0))), hero, [_hostile((1, 0))]) is None
    targeting = replace(_hostile((9, 0)), task=replace(_hostile((9, 0)).task, payload={"target_id": 1}))
    assert rest_in_place_update(_rest_state(hero, targeting), hero, [targeting]) is None


# ---- site 3: tactical_rest eat carried food -----------------------------------------------------------------------------------------------------------------

def _forager(hunger):
    ent = V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(10.0, 10.0).biological(hunger=hunger).inventory(gold=0).build()
    return replace(ent, inventory=replace(ent.inventory, items=[ItemStack("wild_berries", 1)]))


def test_eat_carried_rows():
    pressing, calm = _forager(PRESSING_HUNGER), _forager(CALM_HUNGER + 5.0)
    attacking = TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1})

    def run(entity, task=None):
        h = replace(_hostile((10, 11)), task=task) if task is not None else _hostile((10, 11))
        state = AuthoritativeState(tick=500, seed=1, entities={entity.id: entity, h.id: h})
        return eat_carried_update(entity, [h], state)

    assert run(pressing) is not None                    # pressing, adjacent, not acting: the need wins (changed)
    assert run(pressing, attacking) is None             # acting: the threat wins
    assert run(calm) is None                            # calm and adjacent: AGENCY-07 terms still hold it back
