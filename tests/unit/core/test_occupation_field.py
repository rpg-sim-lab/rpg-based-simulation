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

def test_species_of_reads_kind():
    """M1 step 4: `kind` IS the species id on every build path, so the one species read is `kind` (the mirror `properties["species_id"]` is no longer consulted)."""
    entity = V2EntityBuilder(1).kind("human").properties({"species_id": "elf"}).build()
    assert species_of(entity) == "human"


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


# M1 step 4: every writer of `kind` writes a species id and its occupation (the label, None for a newborn). One test per writer builds one entity through that path.

def test_writer_archetype_factory_writes_the_species_and_the_role_label():
    entity = ArchetypeEntityFactory().build_entity(1, _contract(role_id="guard", kind="human"), EntitySpawnContext())
    assert entity.kind == "human" and entity.identity.occupation == "guard"


def test_writer_archetype_factory_falls_back_to_the_profession_when_there_is_no_role():
    entity = ArchetypeEntityFactory().build_entity(1, _contract(role_id="", profession_id="smith", kind="human"), EntitySpawnContext())
    assert entity.identity.occupation == "smith"


def test_writer_entity_spawner_writes_the_species_and_the_role_id():
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from src.worldassembly.models import ResolvedEntityProfile

    profile = ResolvedEntityProfile(legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, attack_range=1, readiness=100.0, species_id="wolf", role_id="hunter", faction_id="wild", **{"def": 1})
    entity = WorldEntitySpawner()._spawn_legacy_guard(1, profile, EntitySpawnContext(), 42)
    assert entity.kind == "wolf" and entity.identity.occupation == "hunter"


def test_writer_generator_hero_writes_the_species_of_the_hero_archetype_and_the_hero_label():
    entity = EntityGenerator(7).spawn_hero((5.0, 5.0))
    assert entity.kind == "human" and entity.identity.occupation == "hero"


def test_writer_generator_monster_writes_the_species_and_the_label_it_is_given():
    gen = EntityGenerator(7)
    for species, label in (("world_boss", "world_boss"), ("world_boss", "ancient_sentinel"), ("dragonkin", "dragonkin"), ("goblin", "monster")):
        entity = gen.spawn_monster((5.0, 5.0), species=species, occupation=label)
        assert entity.kind == species and entity.identity.occupation == label


def test_writer_generator_natural_creature_offspring_writes_the_species_and_the_spawn_label():
    entity = EntityGenerator(7).spawn_natural_creature_offspring((5.0, 5.0), species="goblin", occupation="goblin_warrior")
    assert entity.kind == "goblin" and entity.identity.occupation == "goblin_warrior"


def test_writer_generator_magical_entity_has_no_label():
    entity = EntityGenerator(7).spawn_magical_demonic_entity((5.0, 5.0))
    assert entity.kind == "magical_demonic_entity" and entity.identity.occupation is None


def test_writer_generator_humanoid_offspring_has_the_parents_species_and_no_label():
    from src.core.state import AuthoritativeState

    entity = EntityGenerator(7).spawn_humanoid_offspring((5.0, 5.0), AuthoritativeState(tick=0, seed=1), "human", 1, 2, 0, None, None, None, 3, 3)
    assert entity.kind == "human" and entity.identity.occupation is None


def test_writer_generator_goblin_keeps_the_label_it_wrote_before():
    entity = EntityGenerator(7).spawn_goblin((5.0, 5.0))
    assert entity.kind == "goblin" and entity.identity.occupation == "goblin"


def test_writer_world_compiler_writes_the_declared_species_and_the_role_label_on_one_tiny_world():
    import os

    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context("unit_faction_tension")
    state, _ = WorldCompiler.compile(spec, 42, context=context)
    assert state.entities
    for e in state.entities.values():
        assert e.kind == e.identity.properties["species_id"]
        assert e.identity.occupation == {getattr(q, "id", f"pop_{i}"): q.role.lower() for i, q in enumerate(spec.entities)}[e.identity.properties["population_id"]]


def test_writer_world_compiler_without_a_context_is_the_legacy_path_kind_is_the_role_label():
    """The context-less compile keeps the pre-step-4 behaviour (kind = the role label, occupation equal to it): the legacy path, owned by
    TCK-20261020-TESTS-THAT-COMPILE-A-WORLD-WITHOUT-THE-CONTENT-CONTEXT-TRIAGE (stage 4b), pinned here so it cannot drift silently."""
    import os

    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    spec, _ = WorldRepository(os.path.join("data", "worlds")).load_world_with_context("unit_faction_tension")
    state, _ = WorldCompiler.compile(spec, 42)
    assert state.entities and all(e.kind == e.identity.occupation for e in state.entities.values())


def test_writer_campaign_runner_writes_the_hero_species_and_label():
    from src.domains.campaigns.runner import SimulationAnalysisRunner
    from src.domains.campaigns.spec import CampaignSpecLoader

    spec = CampaignSpecLoader.load_from_yaml("campaign_id: k2\nseed: 42\nticks: 1\nworld_pack: phase1_adventure_seed\nactors:\n  count: 2\n  start_region: hometown\n  start_level: 1\nexpected_arc_families:\n  - cautious_growth\nforbidden_behavior:\n  - action_after_death\n")
    state = SimulationAnalysisRunner().run(spec).final_state
    assert state.entities and all(e.kind == "human" and e.identity.occupation == "hero" for e in state.entities.values())


def test_writer_campaign_survivor_rebuild_keeps_the_kind_and_occupation_it_carried():
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.domains.campaigns.state import EntityCarryForward
    from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec

    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = EntityCarryForward(entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True, kind="human", occupation="guard")
    entity = orch._build_initial_state(11, _real_episode_spec()).entities[42]
    assert entity.kind == "human" and entity.identity.occupation == "guard"


# ---- K6d: each typed refusal fires --------------------------------------------------------------------------------------------------------

def test_k6d_a_profile_with_no_species_is_refused():
    from src.core.species import SpeciesNotDeclaredError
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from src.worldassembly.models import ResolvedEntityProfile

    no_species = ResolvedEntityProfile(legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, attack_range=1, readiness=100.0, role_id="hunter", **{"def": 1})
    with pytest.raises(SpeciesNotDeclaredError):
        WorldEntitySpawner()._spawn_legacy_guard(2, no_species, EntitySpawnContext(), 42)


def test_k6d_an_empty_carried_kind_is_refused():
    from src.core.species import SpeciesNotDeclaredError
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.domains.campaigns.state import EntityCarryForward
    from tests.unit.domains.campaigns.test_campaign_orchestrator import _make_manifest, _real_episode_spec

    orch = CampaignOrchestrator(_make_manifest(n_episodes=2))
    orch.state.persistent_entities[42] = EntityCarryForward(entity_id=42, level=4, xp=900, equipment={}, reputation=0.8, alive=True, kind="", occupation="guard")
    with pytest.raises(SpeciesNotDeclaredError):
        orch._build_initial_state(11, _real_episode_spec())


def test_k6d_a_scenario_spec_with_no_species_is_refused(tmp_path):
    from src.core.species import SpeciesNotDeclaredError
    from src.testing.scenario_runner import ScenarioRunner

    spec = tmp_path / "no_species.yaml"
    spec.write_text("scenario_id: no_species\nworld_pack: phase1_adventure_seed\nactors:\n  - id: 1\n    role: HERO\n", encoding="utf-8")
    with pytest.raises(SpeciesNotDeclaredError):
        ScenarioRunner(str(spec), output_dir=str(tmp_path)).execute(ticks=1)


def test_k6d_a_hero_archetype_with_no_species_is_refused(monkeypatch):
    import src.content.hero_species as gen_mod
    from src.core.species import SpeciesNotDeclaredError

    class _Cat:
        @staticmethod
        def get_entity_archetype(_id):
            return type("A", (), {"species": ""})()

    monkeypatch.setattr(gen_mod, "warmed_catalog", lambda: _Cat)
    with pytest.raises(SpeciesNotDeclaredError):
        gen_mod.hero_species_id()


def test_k6d_an_archetype_that_does_not_resolve_is_refused():
    from src.core.species import SpeciesNotDeclaredError
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from src.worldassembly.models import ResolvedEntityProfile

    profile = ResolvedEntityProfile(legacy_role=0, legacy_faction=0, hp=10, max_hp=10, atk=1, attack_range=1, readiness=100.0, archetype_id="no_such_archetype", species_id="human", **{"def": 1})
    with pytest.raises(SpeciesNotDeclaredError):
        WorldEntitySpawner()._spawn_archetype_native(3, profile, EntitySpawnContext(), object(), 42)


# ---- K6c: no src builder chain without .kind( --------------------------------------------------------------------------------------------------

def test_k6c_every_src_builder_chain_names_its_kind():
    """Static: a `V2EntityBuilder(...)` chain in src with no `.kind(` falls to the builder default ("hero"), which is a code-chosen species. The default stays for tests (a
    fixture-policy ticket owns it); nothing in src may rely on it."""
    root = Path(__file__).resolve().parents[3]
    bare = []
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        inner = {id(n.func.value) for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and id(n) not in inner:
                cur, methods = n, []
                while isinstance(cur, ast.Call) and isinstance(cur.func, ast.Attribute):
                    methods.append(cur.func.attr)
                    cur = cur.func.value
                if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) and cur.func.id == "V2EntityBuilder" and "kind" not in methods:
                    bare.append(f"{path.relative_to(root)}:{n.lineno}")
    assert bare == [], bare


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
        "src/entities/checked_builder.py", "src/entities/archetype_factory.py", "src/systems/world_systems/generator.py",
        "src/observability/readiness/harness.py",
        "src/worldassembly/entity_spawner.py", "src/worldbuilding/compiler.py",
        # the scenario fixtures (designer ruling (a), 2026-11-16): tested in test_occupation_fixture_writers.py
        "src/certification/scenarios.py", "src/perf/scenarios.py", "src/testing/scenario_runner.py",
    }, sorted(sites)


def test_k6_k7_every_gate_world_entity_kind_is_a_species_id_and_the_mirror_agrees_at_t0():
    """K6 (kind is a species id, minus the named allowlist: 0 outside) and K7 (kind equals properties["species_id"]: 0 differing), read at build over the three gate worlds
    of `paired.WORLDS` (compile only, no run). K9 at t0: the occupation is the population's role label, the string `kind` held before step 4."""
    import os

    from src.content.common_knowledge_seed import warmed_catalog
    from src.core.species import NON_LIVING_KIND_ALLOWLIST
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository

    from tools.rpg_measure.paired import WORLDS

    species_ids = set(warmed_catalog().species) | set(NON_LIVING_KIND_ALLOWLIST)
    checked = 0
    for world in WORLDS:
        spec, context = WorldRepository(os.path.join("data", "worlds")).load_world_with_context(world)
        state, _ = WorldCompiler.compile(spec, 42, context=context)
        assert state.entities, world
        for entity in state.entities.values():
            assert entity.kind in species_ids, (world, entity.id, entity.kind)
            assert entity.kind == entity.identity.properties["species_id"], (world, entity.id)
            role_of = {getattr(q, "id", f"pop_{i}"): q.role.lower() for i, q in enumerate(spec.entities)}
            assert entity.identity.occupation == role_of[entity.identity.properties["population_id"]], (world, entity.id)
            checked += 1
    assert checked > 100


# ---- copies keep it ------------------------------------------------------------------------------------------------------------------------

def test_the_entity_copies_in_the_archetype_factory_keep_occupation():
    entity = ArchetypeEntityFactory().build_entity(1, _contract(role_id="guard", kind="guard"), EntitySpawnContext())
    from src.core.state import InventoryComponent

    assert _replace_inventory(entity, InventoryComponent(items=(), gold=3)).identity.occupation == "guard"
    assert _replace_lifecycle(entity, active=False).identity.occupation == "guard"


def test_k6c_every_src_spawn_call_passes_a_species_id_not_a_label():
    """Static, rpg-designer 2026-11-17: the spawners do not validate `species`, so every src CALL of spawn_monster / spawn_natural_creature_offspring must pass an id in
    species.yaml (or the named non-living allowlist) as a literal, or a species read from content or from an entity that already carries one (`camp.kind`, `entity.kind`)."""
    from src.content.common_knowledge_seed import warmed_catalog
    from src.core.species import NON_LIVING_KIND_ALLOWLIST

    allowed = set(warmed_catalog().species) | set(NON_LIVING_KIND_ALLOWLIST)
    carried = {"camp.kind", "entity.kind"}
    root = Path(__file__).resolve().parents[3]
    bad, calls = [], 0
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"spawn_monster", "spawn_natural_creature_offspring"}:
                species = [kw.value for kw in n.keywords if kw.arg == "species"]
                calls += 1
                where = f"{path.relative_to(root)}:{n.lineno}"
                if len(species) != 1:
                    bad.append((where, "no species argument"))
                elif isinstance(species[0], ast.Constant):
                    if species[0].value not in allowed:
                        bad.append((where, species[0].value))
                elif ast.unparse(species[0]) not in carried:
                    bad.append((where, ast.unparse(species[0])))
    assert calls >= 7 and bad == [], bad


# ---- the presenter shows both --------------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_summary, StatePresenter.present_entity_slim])
def test_the_presenter_shows_kind_and_occupation(shape):
    out = shape(V2EntityBuilder(1).kind("human").identity(occupation="merchant").location(1.0, 1.0).build())
    assert out["kind"] == "human" and out["occupation"] == "merchant"


@pytest.mark.parametrize("shape", [StatePresenter.present_entity, StatePresenter.present_entity_summary, StatePresenter.present_entity_slim])
def test_the_presenter_shows_null_for_a_body_with_no_label(shape):
    assert shape(V2EntityBuilder(1).kind("human").location(1.0, 1.0).build())["occupation"] is None


# ---- K3: nobody reads the new field yet ----------------------------------------------------------------------------------------------------

# The production files that read the `.occupation` attribute: the carry, copy and presentation sites of step 2 (each for a reason that is not a decision): the field's own canonical dict and read-only copy, the apply path's hand-copy of the record, the builder's
# carry, the campaign carry-forward (extract, save, rebuild), the presenter. Step 3 moves the label readers to `occupation`, and this list is then extended on purpose.
_OCCUPATION_ATTRIBUTE_ALLOWLIST = {
    # the field itself, the carry and the copy sites, the presenter (step 2)
    "src/core/state.py", "src/engine/apply.py", "src/domains/campaigns/orchestrator.py", "src/domains/campaigns/state.py", "src/api/presenters/state_presenter.py",
    "src/domains/campaigns/survivor_rebuild.py",  # moved from orchestrator.py:851 by #968's code-health extraction; same carry-forward read
    # the helper that reads it for the duck-typed readers, and the label readers step 3 moved off `kind` (rpg-designer 665b9718, rows 10-13, 15-23, B1-B3, B5, B9-B12)
    "src/world/calamity.py", "src/world/threat.py", "src/world/environment.py", "src/world/creature_territory.py",
    "src/systems/world_systems/navigation.py",
}


def test_k3_no_production_code_reads_occupation_attribute_outside_the_carry_presentation_and_moved_label_reader_sites():
    root = Path(__file__).resolve().parents[3]
    readers = set()
    for path in sorted((root / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        if any(isinstance(n, ast.Attribute) and n.attr == "occupation" and isinstance(n.ctx, ast.Load) for n in ast.walk(tree)):
            readers.add(str(path.relative_to(root)))
    assert readers == _OCCUPATION_ATTRIBUTE_ALLOWLIST, sorted(readers ^ _OCCUPATION_ATTRIBUTE_ALLOWLIST)
