"""TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT (designer option A): a panic flight, a retreat project's adoption and its completion use ONE test.

`present_threats` (src/engine/tactical_threat.py) is that test: the perceived hostiles when `present_threat_terms` is non-empty, else none. The tactical pass keeps only
those as its flight `threats`; the goal-level `present_threat_to` is the same call over `perceived_hostiles`.
"""
from src.ai.goals.present_threat import present_threat_to
from src.core.enums import Faction
from src.engine.tactical import TacticalDecisionSystem
from src.engine.tactical_threat import perceived_threats, present_threats
from tests.unit.combat.test_tactical_destinations import _entity, _state


def test_a_wounded_subject_has_a_present_threat_from_any_hostile_in_view():
    me = _entity(1, Faction.HERO_GUILD, hp=40, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 26.0))
    assert present_threats(me, perceived_threats(me, [foe])) == [foe]


def test_a_healthy_subject_has_none_from_a_distant_idle_hostile():
    me = _entity(1, Faction.HERO_GUILD, hp=100, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 28.0))
    assert present_threats(me, perceived_threats(me, [foe])) == []


def test_an_adjacent_hostile_is_a_present_threat_at_full_health():
    me = _entity(1, Faction.HERO_GUILD, hp=100, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 21.0))
    assert present_threats(me, perceived_threats(me, [foe])) == [foe]


def test_no_hostiles_is_no_threat():
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    assert present_threats(me, []) == []


def test_the_goal_level_test_is_the_same_call_over_the_perceived_hostiles():
    for hp, foe_y in ((40, 26.0), (100, 28.0), (100, 21.0)):
        me = _entity(1, Faction.HERO_GUILD, hp=hp, pos=(20.0, 20.0))
        foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, foe_y))
        assert present_threat_to(me, _state(me, foe)) == bool(present_threats(me, perceived_threats(me, [foe])))


def test_a_wounded_subject_with_a_hostile_in_view_still_flees():
    """The rule narrows only the no-present-threat case: a wounded subject beside a hostile keeps its PANIC_RETREAT (2.114 unchanged for it)."""
    me = _entity(1, Faction.HERO_GUILD, hp=5, pos=(20.0, 20.0))
    foe = _entity(2, Faction.MONSTER_HORDE, pos=(20.0, 22.0))
    update = TacticalDecisionSystem.evaluate_entity_intent(_state(me, foe), me)
    assert update.task is not None and update.task.payload_set.get("reason") == "PANIC_RETREAT"
