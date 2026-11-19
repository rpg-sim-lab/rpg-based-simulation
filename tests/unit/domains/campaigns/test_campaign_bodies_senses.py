"""TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK, build half (PERC-02a): campaign episode bodies and scenario-runner bodies are
refused at build with SenseProfileError when their species has no usable sense profile, and build exactly as before for a profiled kind."""
from __future__ import annotations

import pytest

from src.core.species import SenseProfileError
from src.domains.campaigns.orchestrator import CampaignOrchestrator
from src.domains.campaigns.runner import SimulationAnalysisRunner
from src.domains.campaigns.spec import CampaignSpecLoader
from src.domains.campaigns.state import EntityCarryForward
from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec

CAMPAIGN = """
campaign_id: senses_check
seed: 42
ticks: 1
world_pack: phase1_adventure_seed
actors:
  count: 1
  start_region: hometown
  start_level: 1
  class_distribution:
    warrior: 1
  trait_distribution:
    brave: 1.0
initial_world_pressures:
  - weak_starting_equipment
expected_arc_families:
  - cautious_growth
forbidden_behavior:
  - action_after_death
"""


def _carry(kind):
    return EntityCarryForward(entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True, kind=kind, role=3, faction=1)


def test_a_campaign_episode_body_of_an_unprofiled_kind_fails_at_build_naming_the_site():
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry("no_such_species_xyz")
    with pytest.raises(SenseProfileError, match="campaign episode body 42"):
        orch._build_initial_state(11, _real_episode_spec())


def test_a_campaign_episode_body_of_a_profiled_kind_builds_as_before():
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry("human")
    assert orch._build_initial_state(11, _real_episode_spec()).entities[42].kind == "human"


def test_the_scenario_runner_refuses_an_unprofiled_hero_species(monkeypatch):
    monkeypatch.setattr("src.domains.campaigns.runner.hero_species_id", lambda: "no_such_species_xyz")
    with pytest.raises(SenseProfileError, match="scenario runner hero 1"):
        SimulationAnalysisRunner().run(CampaignSpecLoader.load_from_yaml(CAMPAIGN))


def test_the_scenario_runner_builds_a_human_hero_as_before():
    result = SimulationAnalysisRunner().run(CampaignSpecLoader.load_from_yaml(CAMPAIGN))
    assert result.final_state is not None
