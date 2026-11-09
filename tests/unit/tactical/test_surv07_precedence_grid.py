"""SURV-07 LAW P precedence grid (TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED).

At every site that weighs a need past its escalation onset against another goal or act, the need wins unless a hostile ACTS on the subject (`need_yields` =
`acting_threat_to`, memo row 88). One grid: {need pressing: yes / no} x {no hostile / perceived only / present, not acting / acting} x site -> winner.
Each "no" row asserts today's behaviour, each pressing and not-acting row asserts that the need wins, each acting row asserts that the threat wins.
Sites in this file: tactical.py presence skip (`if not hostiles:`, the hunger arrival); tactical_rest in-place rest and eat carried food, which keep the full AGENCY-07 terms (memo row 88, S1).
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
    real_rest, real_pursue, real_classify = tactical_module.in_place_survival_update, tactical_module.pursue_objective, tactical_module.classify_neighbours

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
    monkeypatch.setattr(tactical_module, "pursue_objective", spy_pursue)
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


def test_unit_case_13_16_a_subject_at_hunger_80_pursuing_a_fleeing_scout_that_never_attacks_it_keeps_its_hunger_project():
    """ENG item 7, built from the recorded values (s44 trace t1605-1610: subject 13 at hunger 80, past onset, pursues scout 16, which flees and never acts on it)."""
    fleeing = TaskComponent(work_kind="ENTITY_MOVE", payload={"target_position": (39.0, 5.0), "reason": "FLEE_THREAT"})
    state, hero = _hungry_hero(PRESSING_HUNGER, hostile_at=(45.0, 26.0), hostile_task=fleeing, hero_at=(45.0, 31.0))
    hero = replace(hero, task=TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 2}))   # 13 is in ATTACK on 16
    state = AuthoritativeState(tick=1, seed=1, entities={1: hero, 2: state.entities[2]}, buildings=state.buildings, blocked_tiles=state.blocked_tiles,
                               building_tiles={}, terrain={})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    assert update.navigation is not None and update.navigation.target_set == INN        # walks to the inn, keeps its hunger objective
    assert not (update.task and (update.task.payload_set or {}).get("action") == "ATTACK")
    assert update.strategic is None, "the hunger project must not be suspended for a hostile that is not acting on the subject"


# ---- site 1b: the fatigue arrival under the pressing-need path ------------------------------------------------------------------------------------------------

def _sleepy_arrival(beds, hostile_at, hostile_task=None):
    """A hero at sleep_debt 90 (past the onset) one tile from an inn with a fatigue project on it, a hostile at `hostile_at`; `beds` is the inn's declared beds."""
    hero = (V2EntityBuilder(1).kind("HERO").properties({"species_id": "human"}).location(39.0, 31.0).identity(faction=Faction.HERO_GUILD)   # a person: it keeps coin, so a bed can be delivered
            .combat(hp=85, max_hp=85, atk=10, def_stat=5, alive=True, readiness=100.0)
            .navigation(movement_mode=MovementMode.WANDER, target=INN).lifecycle(active=True).build())
    hero = replace(hero, biological=replace(hero.biological, hunger=0.0, sleep_debt=PRESSING_DEBT))
    objective = ObjectiveState(id="fatigue_20003", kind=ObjectiveKind.REACH_LOCATION, target="20003", status=ObjectiveStatus.ACTIVE)
    project = ProjectState(id="proj_fatigue_1", kind="fatigue", status=ProjectStatus.ACTIVE, objectives=[objective], active_objective_id=objective.id)
    hero = replace(hero, strategic=replace(hero.strategic, projects={project.id: project}, current_project_id=project.id, current_objective_id=objective.id))
    monster = (V2EntityBuilder(2).kind("MONSTER").location(*hostile_at).identity(faction=Faction.MONSTER_HORDE)
               .combat(hp=300, max_hp=300, atk=60, def_stat=5, alive=True, readiness=100.0)
               .navigation(movement_mode=MovementMode.WANDER).lifecycle(active=True).build())
    if hostile_task is not None:
        monster = replace(monster, task=hostile_task)
    inn = BuildingState(id=INN_ID, kind="inn", position=INN, functional=True, beds=beds)
    state = AuthoritativeState(tick=1, seed=1, entities={1: hero, 2: monster}, buildings={INN_ID: inn}, blocked_tiles={(40, 31)}, building_tiles={}, terrain={})
    return state, hero


FATIGUE_ROWS = [
    # (beds, hostile position, hostile task, label, dispatches REST)
    (2, (39.0, 30.0), None, "fatigue arrival, the REST lodges, hostile adjacent but not acting", True),
    (2, (39.0, 26.0), None, "fatigue arrival, the REST lodges, hostile perceived only", True),
    (0, (39.0, 26.0), None, "fatigue arrival, no-bed building, AGENCY-07 terms clear", True),
    (0, (39.0, 30.0), None, "fatigue arrival, no-bed building, AGENCY-07 terms true (adjacent)", False),
    (2, (39.0, 30.0), ATTACKS_THE_HERO, "fatigue arrival, the REST lodges, hostile acting (the threat wins)", False),
]


@pytest.mark.parametrize("beds,hostile_at,hostile_task,label,rests", FATIGUE_ROWS, ids=[r[3] for r in FATIGUE_ROWS])
def test_the_fatigue_arrival_row(monkeypatch, beds, hostile_at, hostile_task, label, rests):
    seen = {"hostiles": 0}
    real_classify = tactical_module.classify_neighbours

    def spy_classify(*a, **k):
        hood = real_classify(*a, **k)
        seen["hostiles"] = len(hood.hostiles)
        return hood

    monkeypatch.setattr(tactical_module, "classify_neighbours", spy_classify)
    state, hero = _sleepy_arrival(beds, hostile_at, hostile_task)
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    payload = (update.task.payload_set if update.task is not None else None) or {}
    assert payload.get("reason") != "PANIC_RETREAT" and seen["hostiles"] == 1, "the row must reach the pressing-need path with a hostile in sight"
    if rests:
        assert payload.get("action") == "REST" and payload.get("target_id") == INN_ID, label
    elif hostile_task is None:   # the wait: nothing dispatched, the project stays current (no end, no suspension)
        assert update.task is None and update.strategic is None and update.navigation is None, label
    else:                        # acting: the threat wins
        assert payload.get("action") != "REST", label


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


def test_rest_in_place_pressing_rows_keep_the_agency_07_terms():
    """Memo row 88 (S1): resting or eating in place keeps the FULL AGENCY-07 terms, pressing or not (widening them is SURV-06's question, the owner's). So at
    sleep_debt 90 an adjacent hostile that is not acting, and a hostile targeting by payload alone, still block the rest; only a far, untargeting one does not."""
    hero = _sleepy_hero(PRESSING_DEBT)
    assert _rests(rest_in_place_update(_rest_state(hero), hero, []))                                                   # no hostile
    assert _rests(rest_in_place_update(_rest_state(hero, _hostile((12, 0))), hero, [_hostile((12, 0))]))               # perceived only
    assert rest_in_place_update(_rest_state(hero, _hostile((1, 0))), hero, [_hostile((1, 0))]) is None                 # adjacent, not acting: AGENCY-07 holds it back
    attacking = _hostile((1, 0), TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1}))
    assert rest_in_place_update(_rest_state(hero, attacking), hero, [attacking]) is None                              # acting: the threat wins


def test_rest_in_place_a_hostile_targeting_by_payload_alone_is_not_acting_but_still_blocks_the_rest():
    """The old test's targeting=1 row at distance 9, past the onset: not an act (`acting_threat_to` False, `need_yields` False) and yet AGENCY-07's TARGETED term
    still blocks the rest, so it lands on None (the original expectation), not REST."""
    from src.ai.goals.present_threat import acting_threat_to

    hero = _sleepy_hero(PRESSING_DEBT)
    targeting = replace(_hostile((9, 0)), task=replace(_hostile((9, 0)).task, payload={"target_id": 1}))
    state = _rest_state(hero, targeting)
    assert not acting_threat_to(hero, state)
    assert rest_in_place_update(state, hero, [targeting]) is None


# ---- site 3: tactical_rest eat carried food -----------------------------------------------------------------------------------------------------------------

def _forager(hunger):
    ent = V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).location(10.0, 10.0).biological(hunger=hunger).inventory(gold=0).build()
    return replace(ent, inventory=replace(ent.inventory, items=[ItemStack("wild_berries", 1)]))


def test_eat_carried_rows_keep_the_agency_07_terms():
    pressing, calm = _forager(PRESSING_HUNGER), _forager(CALM_HUNGER + 5.0)
    attacking = TaskComponent(work_kind="ENTITY_ACT", payload={"action": "ATTACK", "target_id": 1})

    def run(entity, hostile_at, task=None):
        h = replace(_hostile(hostile_at), task=task) if task is not None else _hostile(hostile_at)
        return eat_carried_update(entity, [h])

    assert run(pressing, (10, 12)) is not None              # pressing, far hostile: eats
    assert run(pressing, (10, 11)) is None                  # pressing, adjacent, not acting: AGENCY-07 holds it back (row 88 S1)
    assert run(pressing, (10, 11), attacking) is None       # acting: the threat wins
    assert run(calm, (10, 11)) is None                      # calm and adjacent: unchanged


# ---- owner readings 2 and 3 (#715 6697054601), unit rows ---------------------------------------------------------------------------------------------------

def test_reading_2_the_served_meal_on_arrival_is_taken_below_the_consequence_line_with_a_non_acting_hostile_in_sight():
    """Hunger 80 is past the escalation onset and below the consequence line (95). The hero stands one tile from the inn the hunger project names, a hostile that is
    not acting on it stands beside it: on arrival the project's served meal (EAT at the inn) is taken."""
    assert PRESSING_HUNGER < 95.0
    state, hero = _hungry_hero(PRESSING_HUNGER, hostile_at=(39.0, 30.0))
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    payload = (update.task.payload_set if update.task is not None else None) or {}
    assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"



def _hurt_hero(hunger, hp, hostile_at=(39.0, 30.0)):
    state, hero = _hungry_hero(hunger, hostile_at=hostile_at)
    hurt = replace(hero, combat=replace(hero.combat, hp=hp))
    return replace(state, entities={**state.entities, 1: hurt}), hurt


def _payload(state, hero):
    update = TacticalDecisionSystem.evaluate_entity_intent(state, hero)
    return (update.task.payload_set if update.task is not None else None) or {}


def test_reading_3_past_the_consequence_line_a_badly_hurt_subject_with_nothing_acting_takes_the_need_path():
    """Owner reading 3 (#715 6697054601, corrected 6697215821): hp 8 of 85 (under 15%), hunger 96 (past the line), a hostile not acting on it: the need path, EAT."""
    payload = _payload(*_hurt_hero(96.0, 8))
    assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"


def test_reading_3_below_the_consequence_line_a_panic_with_nowhere_to_go_does_not_freeze_against_a_pressing_need():
    """Row 88 (5) and the closed gap (TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE, rpg-designer scope 2(c)): hp 8 of 85,
    hunger 80 (pressing, below the line), a hostile not acting on it, no destination: the panic does not freeze, the tick takes the need path, EAT at the inn. A panic WITH a
    destination still flees (test_low_hp_retreat_gate.py)."""
    payload = _payload(*_hurt_hero(PRESSING_HUNGER, 8))
    assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"


@pytest.mark.parametrize("hp", [20, 30])
def test_control_not_reading_3_above_the_panic_health_a_pressing_subject_eats(hp):
    """Control, not part of reading 3: at hp 20 and 30 of 85 `is_fleeing` is False, so the panic branch does not run and the need path eats (hunger 80)."""
    payload = _payload(*_hurt_hero(PRESSING_HUNGER, hp))
    assert payload.get("action") == "EAT" and payload.get("target_id") == INN_ID, f"got {payload}"
