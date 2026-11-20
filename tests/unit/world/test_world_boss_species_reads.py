# Compliance IDs: WORLD-122
"""TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS: the two readers that look for a world boss read its SPECIES (``species_of(entity) == "world_boss"``), not its occupation.

boss.py spawns species "world_boss" with occupation "ancient_sentinel" (boss.py:151-152); calamity.py:83 spawns species "world_boss" with occupation "world_boss". Each reader must find both bodies.
"""
import dataclasses

import pytest

from src.core.builder import V2EntityBuilder
from src.core.state import AuthoritativeState, RegionState
from src.systems.world_systems.navigation import FlowFieldService
from src.world.threat import ThreatService

BOSS_POSITION = (33.0, 44.0)


def _boss(entity_id, occupation, active=True, alive=True):
    body = V2EntityBuilder(entity_id).kind("world_boss").location(*BOSS_POSITION).identity(occupation=occupation).combat(alive=alive).build()
    return dataclasses.replace(body, lifecycle=dataclasses.replace(body.lifecycle, active=active))


def _state(*bodies):
    return AuthoritativeState(tick=1, seed=42, entities={b.id: b for b in bodies}, next_entity_id=max(b.id for b in bodies) + 1)


@pytest.fixture
def no_fixed_world_boss_anchor(monkeypatch):
    """FlowFieldService.ANCHORS carries a fixed WORLD_BOSS waypoint pair, which makes the dynamic-boss fallback in get_flow_direction unreachable for the WORLD_BOSS target; the fallback is
    exercised here with that fixed pair removed (the reader is what this ticket fixes, not the anchor table)."""
    monkeypatch.setattr(FlowFieldService, "ANCHORS", {k: v for k, v in FlowFieldService.ANCHORS.items() if k != "WORLD_BOSS"})


@pytest.mark.parametrize("occupation", ["ancient_sentinel", "world_boss"])  # a boss.py-spawned boss, and a calamity-style one (occupation equal to its species)
def test_navigation_finds_a_world_boss_by_its_species(no_fixed_world_boss_anchor, occupation):
    state = _state(V2EntityBuilder(1).kind("human").location(0.0, 0.0).build(), _boss(2, occupation))
    direction = FlowFieldService.get_flow_direction((0.0, 0.0), "WORLD_BOSS", state)
    assert direction is not None  # the boss at (33, 44) was found as the anchor: a unit vector towards it
    assert direction == pytest.approx((33.0 / 55.0, 44.0 / 55.0))


def test_navigation_does_not_take_another_species_for_a_world_boss(no_fixed_world_boss_anchor):
    state = _state(V2EntityBuilder(1).kind("human").location(0.0, 0.0).build(), V2EntityBuilder(2).kind("goblin").location(*BOSS_POSITION).identity(occupation="world_boss").build())
    assert FlowFieldService.get_flow_direction((0.0, 0.0), "WORLD_BOSS", state) is None  # a goblin whose occupation says "world_boss" is not a world boss


def _region():
    return RegionState(id="r", name="R", bounds=(0, 0, 10, 10), trauma_score=5.0, retaliation_pressure=0.0)


@pytest.mark.parametrize("occupation", ["ancient_sentinel", "world_boss"])
def test_threat_sees_a_living_active_world_boss_by_its_species_so_trauma_does_not_decay(occupation):
    state = _state(_boss(2, occupation))
    assert ThreatService.process_threat_evolution(state, _region()) is None  # a boss in the world is not peaceful: no decay, nothing changed


@pytest.mark.parametrize("kwargs", [{"active": False}, {"alive": False}])
def test_threat_keeps_its_active_and_alive_conditions(kwargs):
    state = _state(_boss(2, "ancient_sentinel", **kwargs))
    update = ThreatService.process_threat_evolution(state, _region())
    assert update is not None and update.trauma_delta == -ThreatService.THREAT_DECAY_RATE  # an inactive or dead boss leaves the region peaceful


def test_threat_decays_trauma_when_there_is_no_boss_at_all():
    state = _state(V2EntityBuilder(1).kind("human").location(1.0, 1.0).build())
    update = ThreatService.process_threat_evolution(state, _region())
    assert update is not None and update.trauma_delta == -ThreatService.THREAT_DECAY_RATE
