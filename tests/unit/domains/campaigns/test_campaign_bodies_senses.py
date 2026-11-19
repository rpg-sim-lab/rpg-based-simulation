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


@pytest.fixture()
def break_profile():
    """Returns a function that installs the warmed catalog with the named in-content species declaring a sense profile that does not exist."""
    from src.content.repository import CatalogRepository
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers

    def _break(species_id):
        repo = CatalogRepository("data/content")
        repo.load_all()
        repo.species[species_id] = repo.species[species_id].model_copy(update={"sense_profile": "nope"})
        configure_behavior_consumers(repo)

    try:
        yield _break
    finally:
        reset_behavior_consumers()


def test_a_campaign_episode_body_of_a_species_in_content_with_no_usable_profile_fails_at_build_naming_the_site(break_profile):
    break_profile("slime")  # in content, in no compiled world, so the compile path does not reach it first
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry("slime")
    with pytest.raises(SenseProfileError, match="campaign episode body 42"):
        orch._build_initial_state(11, _real_episode_spec())


def test_a_campaign_episode_body_of_a_profiled_kind_builds_as_before():
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry("human")
    assert orch._build_initial_state(11, _real_episode_spec()).entities[42].kind == "human"


def test_an_unknown_kind_perceives_with_the_baseline_and_builds():
    """2.210 item 3: a kind not in content is a fixture; the campaign and runner sites do not refuse it (restore does)."""
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = _carry("no_such_species_xyz")
    assert orch._build_initial_state(11, _real_episode_spec()).entities[42].kind == "no_such_species_xyz"


def test_the_scenario_runner_refuses_a_hero_species_in_content_with_no_usable_profile(break_profile):
    break_profile("human")
    with pytest.raises(SenseProfileError, match="scenario runner hero 1"):
        SimulationAnalysisRunner().run(CampaignSpecLoader.load_from_yaml(CAMPAIGN))


def test_the_scenario_runner_builds_a_human_hero_as_before():
    result = SimulationAnalysisRunner().run(CampaignSpecLoader.load_from_yaml(CAMPAIGN))
    assert result.final_state is not None
