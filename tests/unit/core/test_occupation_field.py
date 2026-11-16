"""TCK-20261109-M1-KIND-ALWAYS-MEANS-SPECIES-AND-OCCUPATION-IS-ITS-OWN-FIELD, step 2 (rpg-designer ruling 67cc6f6d, step-1 rulings 665b9718).

`IdentityComponent.occupation` is the role label the content gave the body (a display label, decision 50). It is appended LAST, omitted from the canonical dict while None,
written at build on every path, carried by the survivor rebuild and the entity copies, and shown by the presenter. `species_of` is the one way to read a species. Nothing
in production branches on `occupation` yet (K3, below).
"""
from __future__ import annotations

import ast
import dataclasses
from pathlib import Path

import pytest

from src.api.presenters.state_presenter import StatePresenter
from src.core.builder import V2EntityBuilder
from src.core.species import species_of
from src.core.state import AuthoritativeState, IdentityComponent
from src.engine.checkpoint_fields import FIELD_RULES, fill_missing_fields
from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext, _replace_inventory, _replace_lifecycle
from src.entities.runtime_contract import ResolvedEntityRuntimeContract
from src.systems.world_systems.generator import EntityGenerator


def _labelled(label="worker"):
    return V2EntityBuilder(1).kind("human").identity(occupation=label).location(0.0, 0.0).build()


# ---- the field -----------------------------------------------------------------------------------------------------------------------------

def test_occupation_is_the_last_field_of_the_identity_and_defaults_to_none():
    names = [f.name for f in dataclasses.fields(IdentityComponent)]
    assert names[-1] == "occupation"
    assert IdentityComponent().occupation is None


def test_the_canonical_dict_omits_occupation_while_none_and_carries_it_once_set():
    bare = IdentityComponent().to_canonical_dict()
    labelled = IdentityComponent(occupation="guard").to_canonical_dict()
    assert "occupation" not in bare
    assert labelled["occupation"] == "guard"
    assert set(labelled) == set(bare) | {"occupation"}


def test_the_builder_writes_it_and_a_later_identity_call_keeps_it():
    entity = V2EntityBuilder(1).kind("human").identity(occupation="merchant").identity(class_id="warrior").build()
    assert entity.identity.occupation == "merchant" and entity.identity.class_id == "warrior"


def test_a_body_built_without_a_label_has_none():
    assert V2EntityBuilder(1).kind("human").build().identity.occupation is None


def test_the_readonly_view_keeps_occupation():
    entity = _labelled("scout")
    assert entity.to_readonly().identity.occupation == "scout"


# ---- the checkpoint rule -------------------------------------------------------------------------------------------------------------------

def test_the_occupation_field_has_a_rule_naming_its_record():
    rows = [r for r in FIELD_RULES if r.field == "occupation"]
    assert len(rows) == 1 and rows[0].record == "IdentityComponent"


def test_an_identity_from_a_checkpoint_that_predates_the_field_restores_to_none_and_keeps_every_other_field():
    entity = _labelled("worker")
    old_identity = IdentityComponent.__new__(IdentityComponent)
    old_names = [f.name for f in dataclasses.fields(IdentityComponent) if f.name != "occupation"]
    IdentityComponent.__setstate__(old_identity, tuple(getattr(entity.identity, n) for n in old_names))
    assert not hasattr(old_identity, "occupation")
    state = AuthoritativeState(tick=0, seed=1, entities={1: dataclasses.replace(entity, identity=old_identity)})
    fill_missing_fields(state)
    restored = state.entities[1].identity
    assert restored.occupation is None
    assert {n: getattr(restored, n) for n in old_names if n != "_canonical_cache"} == {n: getattr(entity.identity, n) for n in old_names if n != "_canonical_cache"}


# ---- species_of ----------------------------------------------------------------------------------------------------------------------------

def test_species_of_reads_the_species_property_on_the_classic_path():
    entity = V2EntityBuilder(1).kind("worker").properties({"species_id": "human"}).build()
    assert species_of(entity) == "human"


def test_species_of_falls_back_to_kind_where_there_is_no_species_property():
    assert species_of(V2EntityBuilder(1).kind("wolf").build()) == "wolf"


def test_species_of_on_the_archetype_path_returns_the_species():
    contract = _contract(species_id="goblin", kind="goblin", role_id="raider")
    entity = ArchetypeEntityFactory().build_entity(1, contract, EntitySpawnContext())
    assert species_of(entity) == "goblin"


# ---- writers -------------------------------------------------------------------------------------------------------------------------------

def _contract(**kw) -> ResolvedEntityRuntimeContract:
    defaults = dict(archetype_id="human_worker", species_id="human", faction_id="town_council", role_id="worker", kind="human",
                    hp=80, max_hp=80, atk=8, def_stat=4, attack_range=1, readiness=100.0, inventory_items={}, starting_gold=0.0, traits=(), themes=())
    defaults.update(kw)
    return ResolvedEntityRuntimeContract(**defaults)


# K2 v1.1 (rpg-designer step-2 review 39dcca3d): in step 2 EVERY writer of `kind` writes the exact same string into `occupation`, because step 3 moves the label readers to
# `occupation` and is neutral only if occupation == today's kind on every built entity. One test per writer builds one entity through that path. The true labels (role_id,
# profession_id; None for newborns and camp offspring and the goblin spawner) arrive in step 4.

def test_writer_archetype_factory_occupation_is_the_kind_string():
    entity = ArchetypeEntityFactory().build_entity(1, _contract(role_id="guard", kind="human"), EntitySpawnContext())
    assert entity.kind == "human" and entity.identity.occupation == entity.kind


def test_writer_entity_spawner_legacy_guard_occupation_is_the_kind_string():
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from src.worldassembly.models import ResolvedEntityProfile

    profile = ResolvedEntityProfile(legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, attack_range=1, readiness=100.0, species_id="wolf", role_id="hunter", faction_id="wild", **{"def": 1})
    entity = WorldEntitySpawner()._spawn_legacy_guard(1, profile, EntitySpawnContext(), 42)
    assert entity.kind == "wolf" and entity.identity.occupation == entity.kind
    no_species = ResolvedEntityProfile(legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, attack_range=1, readiness=100.0, role_id="hunter", **{"def": 1})
    fallback = WorldEntitySpawner()._spawn_legacy_guard(2, no_species, EntitySpawnContext(), 42)
    assert fallback.identity.occupation == fallback.kind


def test_writer_generator_hero_occupation_is_the_kind_string():
    entity = EntityGenerator(7).spawn_hero((5.0, 5.0))
    assert entity.identity.occupation == entity.kind == "hero"


def test_writer_generator_monster_occupation_is_the_kind_string():
    gen = EntityGenerator(7)
    for kind in ("world_boss", "ancient_sentinel", "dragonkin", "monster"):
        entity = gen.spawn_monster((5.0, 5.0), kind=kind)
        assert entity.identity.occupation == entity.kind == kind


def test_writer_generator_natural_creature_offspring_occupation_is_the_kind_string():
    entity = EntityGenerator(7).spawn_natural_creature_offspring((5.0, 5.0), kind="wolf")
    assert entity.identity.occupation == entity.kind == "wolf"


def test_writer_generator_magical_entity_occupation_is_the_kind_string():
    entity = EntityGenerator(7).spawn_magical_demonic_entity((5.0, 5.0), kind="dragonkin")
    assert entity.identity.occupation == entity.kind == "dragonkin"


def test_writer_generator_humanoid_offspring_occupation_is_the_kind_string():
    from src.core.state import AuthoritativeState

    entity = EntityGenerator(7).spawn_humanoid_offspring((5.0, 5.0), AuthoritativeState(tick=0, seed=1), "worker", 1, 2, 0, None, None, None, 3, 3)
    assert entity.identity.occupation == entity.kind == "worker"


def test_writer_generator_goblin_occupation_is_the_kind_string():
    entity = EntityGenerator(7).spawn_goblin((5.0, 5.0))
    assert entity.identity.occupation == entity.kind == "goblin"


def test_writer_world_compiler_occupation_is_the_kind_string_on_one_tiny_world():
    import os

    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context("unit_faction_tension")
    state, _ = WorldCompiler.compile(spec, 42, context=context)
    assert state.entities and all(e.identity.occupation == e.kind for e in state.entities.values())


def test_writer_campaign_runner_occupation_is_the_kind_string():
    from src.domains.campaigns.runner import SimulationAnalysisRunner
    from src.domains.campaigns.spec import CampaignSpecLoader

    spec = CampaignSpecLoader.load_from_yaml("campaign_id: k2\nseed: 42\nticks: 1\nworld_pack: phase1_adventure_seed\nactors:\n  count: 2\n  start_region: hometown\n  start_level: 1\nexpected_arc_families:\n  - cautious_growth\nforbidden_behavior:\n  - action_after_death\n")
    state = SimulationAnalysisRunner().run(spec).final_state
    assert state.entities and all(e.identity.occupation == e.kind == "hero" for e in state.entities.values())


def test_writer_campaign_survivor_rebuild_keeps_the_occupation_it_carried():
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.domains.campaigns.state import EntityCarryForward
    from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec

    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = EntityCarryForward(entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True, kind="guard", occupation="guard")
    entity = orch._build_initial_state(11, _real_episode_spec()).entities[42]
    assert entity.kind == "guard" and entity.identity.occupation == entity.kind


def test_every_production_kind_writer_is_one_of_the_tested_sites():
    """The writers above are the whole list: a new `.kind(...)` builder call in src fails here until it is added to the list and tested (K2 v1.1)."""
    root = Path(__file__).resolve().parents[3]
    sites = set()
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "kind" and len(n.args) == 1:
                base = n.func.value
                while isinstance(base, ast.Call) and isinstance(base.func, ast.Attribute):
                    base = base.func.value
                if isinstance(base, ast.Call) and isinstance(base.func, ast.Name) and base.func.id == "V2EntityBuilder":
                    sites.add(str(path.relative_to(root)))
    assert sites == {
        "src/domains/campaigns/orchestrator.py", "src/domains/campaigns/runner.py", "src/entities/archetype_factory.py", "src/systems/world_systems/generator.py",
        "src/worldassembly/entity_spawner.py", "src/worldbuilding/compiler.py",
        # the scenario fixtures (designer ruling (a), 2026-11-16): tested in test_occupation_fixture_writers.py
        "src/certification/scenarios.py", "src/perf/scenarios.py", "src/testing/scenario_runner.py",
    }, sorted(sites)


def test_every_gate_world_entity_has_an_occupation_equal_to_its_kind_at_t0():
    """K2 (rpg-designer's own-job count): at build, entities whose occupation differs from the pre-step kind string: 0. The classic compiler wrote
    `kind = pop_spec.role.lower()` and now also `occupation = pop_spec.role.lower()`; the three gate worlds of `paired.WORLDS` are read here (compile only, no run)."""
    import os

    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    from tools.rpg_measure.paired import WORLDS

    checked = 0
    for world in WORLDS:
        spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
        state, _ = WorldCompiler.compile(spec, 42, context=context)
        assert state.entities, world
        for entity in state.entities.values():
            assert entity.identity.occupation == entity.kind, (world, entity.id, entity.kind, entity.identity.occupation)
            checked += 1
    assert checked > 100


# ---- copies keep it ------------------------------------------------------------------------------------------------------------------------

def test_the_entity_copies_in_the_archetype_factory_keep_occupation():
    entity = ArchetypeEntityFactory().build_entity(1, _contract(role_id="guard", kind="guard"), EntitySpawnContext())
    from src.core.state import InventoryComponent

    assert _replace_inventory(entity, InventoryComponent(items=(), gold=3)).identity.occupation == "guard"
    assert _replace_lifecycle(entity, active=False).identity.occupation == "guard"


# ---- the presenter shows both --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_summary, StatePresenter.present_entity_slim])
def test_the_presenter_shows_kind_and_occupation(shape):
    out = shape(V2EntityBuilder(1).kind("human").identity(occupation="merchant").location(1.0, 1.0).build())
    assert out["kind"] == "human" and out["occupation"] == "merchant"


@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_summary, StatePresenter.present_entity_slim])
def test_the_presenter_shows_null_for_a_body_with_no_label(shape):
    assert shape(V2EntityBuilder(1).kind("human").location(1.0, 1.0).build())["occupation"] is None


# ---- K3: nobody reads the new field yet ----------------------------------------------------------------------------------------------------

# The only production files that mention `.occupation` after step 2, each for a reason that is not a decision: the field's own canonical dict and read-only copy, the apply path's hand-copy of the record, the builder's
# carry, the campaign carry-forward (extract, save, rebuild), the presenter. Step 3 moves the label readers to `occupation`, and this list is then extended on purpose.
_OCCUPATION_ATTRIBUTE_ALLOWLIST = {
    "src/core/state.py",
    "src/engine/apply.py",
    "src/domains/campaigns/orchestrator.py",
    "src/domains/campaigns/state.py",
    "src/api/presenters/state_presenter.py",
}


def test_k3_no_production_code_reads_occupation_outside_the_carry_and_presentation_sites():
    root = Path(__file__).resolve().parents[3]
    readers = set()
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Attribute) and n.attr == "occupation" and isinstance(n.ctx, ast.Load) for n in ast.walk(tree)):
            readers.add(str(path.relative_to(root)))
    assert readers == _OCCUPATION_ATTRIBUTE_ALLOWLIST, sorted(readers ^ _OCCUPATION_ATTRIBUTE_ALLOWLIST)
