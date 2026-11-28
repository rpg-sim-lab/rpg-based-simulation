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


# ---- the real flow: a newborn produced by the births apply path in an episode, carried into the next roster -----------------------------------------

def _episode_with_a_real_birth(monkeypatch):
    """Run the real kernel on frontier_living_world with the birth chance forced to 1 until a newborn exists; return (final_state, t0 ids)."""
    from src.config.profiles import PROD_SMALL
    from src.engine.kernel import Kernel
    from src.platform.rng import DeterministicRNG
    from src.world import births
    from tools.calibrate_simq import _load_world_state

    real = births.get_catalog()

    class _CertainCatalog:
        def get_reproduction_profile(self, profile_id):
            return real.get_reproduction_profile(profile_id).model_copy(update={"birth_chance_per_check": 1.0, "gestation_ticks": 30, "mate_gate": "none", "min_mutual_sentiment": None})

        def __getattr__(self, name):
            return getattr(real, name)

    monkeypatch.setattr(births, "get_catalog", lambda: _CertainCatalog())
    state, _ = _load_world_state("frontier_living_world", seed=42)
    t0_ids = set(state.entities)
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    try:
        for _ in range(61):
            kernel.tick_once()
        return kernel.state, t0_ids
    finally:
        kernel.shutdown()


def _carry_into_next_roster(final_state):
    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities.update(orch._extract_entity_carry_forwards(final_state))
    return orch


def test_real_flow_every_t0_id_precedes_the_newborn_in_the_final_state_and_in_the_rebuilt_roster(monkeypatch):
    final_state, t0_ids = _episode_with_a_real_birth(monkeypatch)
    newborns = [eid for eid, e in final_state.entities.items() if e.lifecycle.parent_a_entity_id is not None and eid not in t0_ids]
    assert newborns, "precondition: the births apply path produced a newborn in the episode"
    order = list(final_state.entities)
    survivors_t0 = [eid for eid in order if eid in t0_ids]
    assert max(order.index(t) for t in survivors_t0) < min(order.index(n) for n in newborns)

    orch = _carry_into_next_roster(final_state)
    roster = list(orch._get_spawn_entities())
    assert max(roster.index(t) for t in roster if t in t0_ids) < min(roster.index(n) for n in newborns if n in roster)

    state = orch._build_initial_state(7, _real_episode_spec(world_id="frontier_living_world"))
    for response in state.pending_information_responses:
        assert response["actor_id"] in t0_ids


def _round_trip(orch, sort_keys):
    from src.domains.campaigns.state import CampaignState
    import json

    return CampaignState.from_dict(json.loads(json.dumps(orch.state.to_dict(), sort_keys=sort_keys)))


def test_a_campaign_state_round_trip_rebuilds_the_roster_in_serialized_key_order(monkeypatch):
    final_state, t0_ids = _episode_with_a_real_birth(monkeypatch)
    orch = _carry_into_next_roster(final_state)
    plain = list(_round_trip(orch, sort_keys=False).persistent_entities)
    assert plain == list(orch.state.persistent_entities)  # to_dict writes ascending ids; a plain dump keeps them
    keyed = list(_round_trip(orch, sort_keys=True).persistent_entities)
    assert keyed == sorted(plain, key=str)  # key-sorted JSON is lexicographic: "100" sorts before "99", which can put a newborn first
