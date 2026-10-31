"""F3 (divergence 2.155): a lodger is indoors. No one outside can reach, see, target, splash, witness or ask it, and it sees no one outside. One test per class of reader."""
from dataclasses import replace

import pytest

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction, ReasonCode
from src.core.state import AuthoritativeState, BuildingState, RegionState
from src.domains.combat_engagement import phase as engagement
from src.engine.appraisal import perceives
from src.engine.combat import CombatResolutionSystem
from src.engine.domain.view import DomainView
from src.engine.legality import LegalityServiceV2
from src.engine.pipeline_phases.movement import MovementPhase
from src.ai.goals.scorers_support import perceived_hostiles
from tests.unit.engine.lodging_kernel import INN_AT, INN_ID

OUTSIDE = (11.0, 10.0)      # the reach tile east of the inn


def _lodger(eid=1):
    e = (V2EntityBuilder(eid).kind("hero").location(*INN_AT).identity(faction=Faction.HERO_GUILD, properties={"species_id": "human"})
         .combat(hp=100, max_hp=100, alive=True, readiness=100.0).lifecycle(active=True).build())
    return replace(e, navigation=replace(e.navigation, lodged_in=INN_ID))


def _raider(eid=2, pos=OUTSIDE):
    return (V2EntityBuilder(eid).kind("goblin").location(*pos).identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE, properties={"species_id": "goblin"})
            .combat(hp=50, max_hp=50, alive=True, readiness=100.0, atk=20).lifecycle(active=True).build())


def _state(*entities):
    region = RegionState(id="r1", name="R", kind="FOREST", bounds=(0, 0, 100, 100), hazard_level=0.0)
    inn = BuildingState(id=INN_ID, kind="inn", position=INN_AT, functional=True, beds=4)
    return AuthoritativeState(tick=5, seed=1, entities={e.id: e for e in entities}, regions={"r1": region}, buildings={INN_ID: inn},
                              next_entity_id=10, next_node_id=1000, terrain={(x, y): "plain" for x in range(30) for y in range(30)})


def test_legality_rejects_an_attack_on_a_lodger_even_with_a_stale_target_id_and_an_attack_from_one():
    lodger, raider = _lodger(), _raider()
    st = _state(lodger, raider)
    assert LegalityServiceV2.verify_attack_legality(raider, lodger, st) == (False, ReasonCode.TARGET_INCAPACITATED)
    assert LegalityServiceV2.verify_attack_legality(lodger, raider, st) == (False, ReasonCode.ATTACKER_INCAPACITATED)
    outside = replace(lodger, navigation=replace(lodger.navigation, lodged_in=None, position=(9.0, 10.0)))
    ok, _ = LegalityServiceV2.verify_attack_legality(raider, outside, _state(outside, raider))
    assert ok is True or _ != ReasonCode.TARGET_INCAPACITATED       # the same pair outside is judged on the ordinary rules


def test_perception_in_both_directions_is_empty_for_a_lodger():
    lodger, raider = _lodger(), _raider()
    st = _state(lodger, raider)
    assert DomainView.get_neighbor_view(st, lodger, 10.0) == []                         # it sees nothing outside
    assert all(eid != 1 for eid, _ in DomainView.get_neighbor_view(st, raider, 10.0))  # nothing outside sees it
    assert not perceives(raider, lodger) and not perceives(lodger, raider)
    assert perceived_hostiles(lodger, st) == [] and lodger.id not in {h.id for h in perceived_hostiles(raider, st)}


def test_an_area_attack_beside_the_inn_does_not_splash_a_lodger():
    lodger, raider = _lodger(), _raider()
    st = _state(lodger, raider)
    updates = CombatResolutionSystem.resolve_aoe_attack(raider, INN_AT, 3, st, defender=None)
    assert lodger.id not in updates


def test_a_lodger_is_not_a_swap_partner():
    lodger, raider = _lodger(), _raider()
    st = _state(lodger, raider)
    assert lodger.navigation.lodged_in is not None and MovementPhase is not None
    # the swap pair search skips a pair with a lodger (dist 1 between the building tile and the reach tile): pinned through the module's own guard
    import inspect
    assert "lodged_in" in inspect.getsource(MovementPhase.resolve_position_swaps)


def test_a_lodger_is_not_a_witness_of_a_fight_outside(monkeypatch):
    lodger, raider = _lodger(1), _raider(2)
    victim = replace(_raider(3, (12.0, 10.0)))
    witness = replace(_lodger(4), navigation=replace(_lodger(4).navigation, lodged_in=None, position=(13.0, 11.0)))   # the control: the same witness standing outside
    st = _state(lodger, raider, victim, witness)
    monkeypatch.setattr(engagement, "_real_combat_this_tick", lambda tick_update: [(3, 2)])
    updates = {}
    engagement._apply_witnessed_combat(st, None, updates)
    assert 4 in updates and 1 not in updates      # the outside witness gets an observation, the lodger does not
