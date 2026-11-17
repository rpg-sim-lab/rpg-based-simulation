"""TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD, step 2: the campaign survivor rebuild carries `identity.occupation`
like the other identity fields (ID-02 survivor-equivalence: a reconstructed survivor must be identity-equivalent to a spawned entity; rpg-designer step-1 ruling, finding 1).
"""
from __future__ import annotations

from src.core.builder import V2EntityBuilder
from src.domains.campaigns.orchestrator import CampaignOrchestrator
from src.domains.campaigns.state import EntityCarryForward
from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec


def _carry(**kw) -> EntityCarryForward:
    base = dict(entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True, kind="human", role=3, faction=1)
    base.update(kw)
    return EntityCarryForward(**base)


def test_the_carry_forward_round_trips_an_occupation():
    cf = _carry(occupation="guard")
    assert cf.to_dict()["occupation"] == "guard"
    assert EntityCarryForward.from_dict(cf.to_dict()).occupation == "guard"


def test_a_carry_forward_without_a_label_serialises_exactly_as_before():
    cf = _carry()
    assert "occupation" not in cf.to_dict()
    assert EntityCarryForward.from_dict(cf.to_dict()).occupation is None
    assert EntityCarryForward.from_dict({k: v for k, v in cf.to_dict().items()}).to_dict() == cf.to_dict()


def test_the_extraction_reads_the_occupation_off_a_real_entity():
    entity = V2EntityBuilder(7).kind("human").identity(occupation="merchant").location(3.0, 4.0).build()
    final_state = type("S", (), {"entities": {7: entity}})()
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    assert orch._extract_entity_carry_forwards(final_state)[7].occupation == "merchant"


def test_a_survivor_rebuilt_from_a_carry_forward_keeps_its_occupation():
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry(occupation="guard")
    state = orch._build_initial_state(11, _real_episode_spec())
    assert state.entities[42].identity.occupation == "guard"


def test_a_survivor_rebuilt_from_a_record_with_no_label_has_none():
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry()
    state = orch._build_initial_state(11, _real_episode_spec())
    assert state.entities[42].identity.occupation is None
