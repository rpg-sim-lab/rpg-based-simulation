# Compliance IDs: WORLD-122
"""What a newborn does to pending-information resolution (M1 births, G1 addendum A1).

A newborn copies its mother's `population_id`, so in campaign mode it can be the roster member that
`WorldCompiler.resolve_pending_information` picks for its population. The resolver is not changed; these tests pin what it does.
"""
import json
import tempfile
from pathlib import Path

import yaml

from src.domains.campaigns.state import EntityCarryForward
from src.observability.reporting.artifact_repository import RunArtifactRepository
from src.observability.warehouse.provenance_lookup import ProvenanceLookupService
from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec
from src.domains.campaigns.orchestrator import CampaignOrchestrator

_POPULATION = "frontier_village_population_frontier_guard"


def _survivor(entity_id: int) -> EntityCarryForward:
    return EntityCarryForward(
        entity_id=entity_id, level=2, xp=100, equipment={}, reputation=0.5, alive=True,
        kind="human", properties={"population_id": _POPULATION},
    )


def _resolved_actor(*entity_ids: int) -> int:
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    for entity_id in entity_ids:
        orch.state.persistent_entities[entity_id] = _survivor(entity_id)
    state = orch._build_initial_state(7, _real_episode_spec(world_id="frontier_living_world"))
    return state.pending_information_responses[0]["actor_id"]


def test_provenance_lookup_leaves_a_newborn_id_past_the_t0_count_unresolved():
    with tempfile.TemporaryDirectory() as tmpdir:
        service = ProvenanceLookupService(run_repo=RunArtifactRepository(base_dir=tmpdir))
        run_dir = Path(tmpdir) / "run_newborn"
        run_dir.mkdir()
        world = {
            "schema_version": "worldspec.v1", "world_id": "w", "name": "W",
            "regions": [{"id": "town_square", "bounds": [0, 0, 10, 10], "type": "town"}],
            "factions": [], "resources": [], "buildings": [],
            "entities": [{"id": "citizens", "spawn_region": "town_square", "role": "citizen", "faction": "town_council", "count": 2}],
            "topology": {"width": 100, "height": 100, "coordinate_system": "grid"},
        }
        (run_dir / "world.resolved.yaml").write_text(yaml.safe_dump(world), encoding="utf-8")
        (run_dir / "run_manifest.json").write_text(json.dumps({
            "run_id": "run_newborn", "scenario_name": "T", "scenario_type": "test", "seed": 42, "status": "COMPLETED",
            "ticks_requested": 10, "started_at": "2026-05-30T12:00:00Z", "observability_mode": "full",
            "resolved_world_path": str(run_dir / "world.resolved.yaml"),
        }), encoding="utf-8")
        (run_dir / "provenance_manifest.json").write_text(json.dumps({
            "manifest_id": "m", "world_id": "w", "catalog_fingerprint": "c",
            "records": {"citizens": {"source_module": "core_town", "recipe_type": "population"}},
        }), encoding="utf-8")

        assert service.get_entity_origin("run_newborn", "2")["element_id"] == "citizens"
        assert service.get_entity_origin("run_newborn", "3") is None


def test_a_roster_holding_only_a_newborn_resolves_the_pending_response_to_the_newborn():
    assert _resolved_actor(150) == 150


def test_a_roster_with_a_t0_member_and_a_newborn_resolves_to_the_first_in_roster_order():
    # The resolver takes the first match in roster (dict insertion) order; nothing sorts the roster by id.
    assert _resolved_actor(99, 150) == 99
    assert _resolved_actor(150, 99) == 150
