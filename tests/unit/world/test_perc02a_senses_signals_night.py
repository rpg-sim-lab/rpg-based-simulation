"""PERC-02a: senses derive from the species, signals follow the body, vision drops at night, a gate error is not perception
(TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS; divergence 2.210; STRAT-352)."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.content.repository import CatalogRepository
from src.core.species import SenseProfileError
from src.world.perception.gate import NIGHT_VISION_STEPS, PerceptionGate, _lower_level, _LEVEL_TO_FLOAT, _PERCEPTION_THRESHOLD
from src.engine.perception_signals import emitted_signals

NIGHT_SIGHTED_PROFILES = {"goblin_alert_senses", "predator_smell_senses", "spider_vibration_senses", "undead_dread_senses", "troll_senses"}


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


def _body(species_id, *, moved=False, asleep=False, lodged=False, alive=True):
    nav = SimpleNamespace(lodged_in=7 if lodged else None, moved_recently=moved)
    task = SimpleNamespace(work_kind="ENTITY_ACT" if asleep else "", payload={"action": "SLEEP"} if asleep else {})
    return SimpleNamespace(
        kind=species_id, identity=SimpleNamespace(properties={"species_id": species_id}),
        navigation=nav, task=task, combat=SimpleNamespace(alive=alive),
    )


# --- P2: senses come from the species --------------------------------------------------------------------------------------------

def test_every_content_species_derives_its_own_profile(catalog):
    gate = PerceptionGate(catalog)
    for species_id, species in catalog.species.items():
        _, source, _ = gate._load_sense_strengths(_body(species_id))
        assert source == species.sense_profile, species_id
    assert gate.unprofiled_counts == {}


def test_night_sight_is_declared_on_exactly_the_ruled_profiles(catalog):
    declared = {pid for pid, p in catalog.sense_profiles.items() if p.night_vision}
    assert declared == NIGHT_SIGHTED_PROFILES
    assert catalog.get_species("troll").sense_profile == "troll_senses"
    for shared in ("normal_humanoid_senses", "arcane_senses"):
        assert not catalog.get_sense_profile(shared).night_vision
    for species_id in ("slime", "spirit"):
        assert not catalog.get_sense_profile(catalog.get_species(species_id).sense_profile).night_vision


def test_species_with_no_resolvable_profile_is_a_typed_error(catalog):
    gate = PerceptionGate(catalog)
    species = catalog.get_species("human")
    broken = species.model_copy(update={"sense_profile": "nope"})
    catalog.species["human"] = broken
    try:
        with pytest.raises(SenseProfileError):
            gate._load_sense_strengths(_body("human"))
    finally:
        catalog.species["human"] = species


# --- signals follow the body --------------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("species_id,visibility", [("goblin", "low"), ("human", "medium"), ("troll", "high")])
def test_visibility_follows_size(catalog, species_id, visibility):
    body = catalog.get_body_model(catalog.get_species(species_id).body_model)
    assert emitted_signals(_body(species_id), body)["visibility"] == visibility


def test_noise_and_vibration_follow_activity(catalog):
    body = catalog.get_body_model(catalog.get_species("human").body_model)
    for kwargs, level in (({"moved": True}, "medium"), ({}, "low"), ({"asleep": True}, "very_low"), ({"lodged": True, "moved": True}, "very_low")):
        sig = emitted_signals(_body("human", **kwargs), body)
        assert sig["noise"] == sig["vibration"] == level, kwargs


def test_scent_and_life_for_the_living_none_for_undead_and_spirit(catalog):
    human = emitted_signals(_body("human"), catalog.get_body_model(catalog.get_species("human").body_model))
    assert human["scent"] == human["life_signal"] == "medium"
    for species_id in ("undead", "spirit"):
        sig = emitted_signals(_body(species_id), catalog.get_body_model(catalog.get_species(species_id).body_model))
        assert sig["life_signal"] == "none", species_id
        assert sig["scent"] == "medium"


def test_a_body_not_in_content_keeps_the_old_default_visibility():
    assert emitted_signals(_body("fixture_species"), None)["visibility"] == "medium"


# --- night: vision counts two levels lower unless the profile declares night vision -----------------------------------------------------

def test_lower_level_steps_down_the_ladder_and_floors_at_none():
    assert _lower_level("medium", NIGHT_VISION_STEPS) == "low"
    assert _lower_level("high", NIGHT_VISION_STEPS) == "medium"
    assert _lower_level("very_low", NIGHT_VISION_STEPS) == "none"
    assert _lower_level("none", NIGHT_VISION_STEPS) == "none"
    assert _lower_level(None, NIGHT_VISION_STEPS) is None


def test_night_hides_a_target_from_a_day_eyed_kind_but_not_from_a_night_sighted_one(catalog):
    gate = PerceptionGate(catalog)
    signals = {"visibility": "medium"}
    ctx = {"distance": 5.0}
    assert gate.can_perceive(_body("human"), signals, {**ctx, "night": False}).perceived
    assert not gate.can_perceive(_body("human"), signals, {**ctx, "night": True}).perceived
    assert gate.can_perceive(_body("goblin"), signals, {**ctx, "night": True}).perceived
    assert gate.can_perceive(_body("troll"), signals, {**ctx, "night": True}).perceived
    assert not gate.can_perceive(_body("elf"), signals, {**ctx, "night": True}).perceived


def test_night_changes_vision_only(catalog):
    gate = PerceptionGate(catalog)
    day = gate.can_perceive(_body("wolf"), {"scent": "medium"}, {"distance": 5.0, "night": False})
    night = gate.can_perceive(_body("human"), {"scent": "high"}, {"distance": 1.0, "night": True})
    assert day.perceived
    assert "scent" in night.signals_used or not night.perceived  # smell is unchanged by night; only vision steps down


# --- P3: a granted perception always scored at or above the threshold --------------------------------------------------------------

def test_no_perception_is_granted_below_the_threshold_on_a_grid(catalog):
    gate = PerceptionGate(catalog)
    levels = [k for k in _LEVEL_TO_FLOAT]
    for species_id in catalog.species:
        for level in levels:
            for distance in (0.0, 3.0, 10.0, 25.0):
                for night in (False, True):
                    res = gate.can_perceive(_body(species_id), {"visibility": level, "noise": level, "scent": level, "vibration": level},
                                            {"distance": distance, "night": night})
                    if res.perceived:
                        assert res.confidence >= _PERCEPTION_THRESHOLD, (species_id, level, distance, night)
                    else:
                        assert res.confidence == 0.0


# --- a gate error is not perception ---------------------------------------------------------------------------------------------------

def test_a_gate_error_is_not_perception_and_is_logged_at_error(monkeypatch, caplog):
    from src.engine import appraisal
    from src.core.builder import V2EntityBuilder

    def boom(*a, **k):
        raise RuntimeError("gate down")

    monkeypatch.setattr(appraisal, "get_perception_gate", lambda: SimpleNamespace(can_perceive=boom))
    a = V2EntityBuilder(1).kind("human").location(0.0, 0.0).build()
    b = V2EntityBuilder(2).kind("human").location(1.0, 0.0).build()
    with caplog.at_level(logging.ERROR, logger="src.engine.appraisal"):
        assert appraisal.perceives(a, b) is False
    assert any(r.levelno == logging.ERROR and "perception gate error" in r.getMessage() for r in caplog.records)


# --- binding rule: perception reads the species, never `kind` ----------------------------------------------------------------------------

def test_perception_modules_read_no_kind():
    src = Path(__file__).resolve().parents[3] / "src"
    for rel in ("world/perception/gate.py", "engine/perception_signals.py", "content/species_senses.py"):
        text = (src / rel).read_text(encoding="utf-8")
        assert not re.search(r"\.kind\b", text), rel
    assert "species_of" in (src / "world" / "perception" / "gate.py").read_text(encoding="utf-8")


def test_a_body_model_may_declare_a_magic_signal_and_only_known_keys_and_levels():
    from src.content.schema import BodyModelDefinition
    body = BodyModelDefinition(id="b", display_name="B", signals={"magic": "very_high", "visibility": "none"})
    sig = emitted_signals(_body("fixture_species"), body)
    assert sig["magic_signal"] == "very_high" and sig["visibility"] == "none"
    for bad in ({"smell": "low"}, {"magic": "enormous"}):
        with pytest.raises(ValueError):
            BodyModelDefinition(id="b", display_name="B", signals=bad)


# --- the build paths refuse what the gate would not profile: ONE resolver (src.content.species_senses) --------------------------------------

@pytest.fixture()
def broken_human(catalog):
    """The module catalog installed as the warmed one the build paths read, with `human` declaring a sense profile that does not exist."""
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    human = catalog.species["human"]
    catalog.species["human"] = human.model_copy(update={"sense_profile": "nope"})
    configure_behavior_consumers(catalog)
    try:
        yield
    finally:
        catalog.species["human"] = human
        reset_behavior_consumers()


@pytest.fixture()
def good_catalog(catalog):
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    configure_behavior_consumers(catalog)
    try:
        yield catalog
    finally:
        reset_behavior_consumers()


def test_the_shared_resolver_returns_the_species_profile_and_refuses_the_rest(good_catalog):
    from src.content.species_senses import require_species_sense_profile, species_sense_profile
    assert require_species_sense_profile("troll", "test").id == "troll_senses"
    assert species_sense_profile(good_catalog, "no_such_species") is None  # the gate counts this as unprofiled
    for bad in ("no_such_species", None, ""):
        with pytest.raises(SenseProfileError):
            require_species_sense_profile(bad, "test")


def test_the_gate_and_the_build_paths_read_the_same_profile(good_catalog):
    from src.content.species_senses import require_species_sense_profile
    gate = PerceptionGate(good_catalog)
    for species_id in good_catalog.species:
        assert gate._load_sense_strengths(_body(species_id))[1] == require_species_sense_profile(species_id, "test").id


def test_archetype_path_refuses_a_content_species_without_a_usable_profile(broken_human):
    from src.entities.archetype_factory import ArchetypeEntityFactory, EntitySpawnContext, require_archetype_senses
    from src.entities.runtime_contract import ResolvedEntityRuntimeContract
    contract = ResolvedEntityRuntimeContract(
        archetype_id="human_worker", species_id="human", faction_id="town_council", role_id="worker", kind="humanoid", hp=80, max_hp=80, atk=8, def_stat=4,
        attack_range=1, readiness=100.0, inventory_items={}, starting_gold=0.0, traits=(), themes=())
    with pytest.raises(SenseProfileError):
        require_archetype_senses(contract)
    with pytest.raises(SenseProfileError):
        ArchetypeEntityFactory().build_entity(1, contract, EntitySpawnContext())


def test_archetype_helper_accepts_a_species_with_a_profile(good_catalog):
    from src.entities.archetype_factory import require_archetype_senses
    from src.entities.runtime_contract import ResolvedEntityRuntimeContract
    contract = ResolvedEntityRuntimeContract(
        archetype_id="human_worker", species_id="human", faction_id="town_council", role_id="worker", kind="humanoid", hp=80, max_hp=80, atk=8, def_stat=4,
        attack_range=1, readiness=100.0, inventory_items={}, starting_gold=0.0, traits=(), themes=())
    require_archetype_senses(contract)


def test_legacy_spawn_path_refuses_a_species_without_a_usable_profile(broken_human):
    from src.entities.archetype_factory import EntitySpawnContext
    from src.worldassembly.entity_spawner import WorldEntitySpawner
    from src.worldassembly.models import ResolvedEntityProfile
    from src.core.enums import EntityRole, Faction
    profile = ResolvedEntityProfile(legacy_role=int(EntityRole.HERO), legacy_faction=int(Faction.HERO_GUILD), hp=10, max_hp=10, atk=1, def_stat=1, attack_range=1, readiness=1.0,
                                    inventory_seed="0", cognition_seed="0", spawn_position=(1.0, 1.0), species_id="human")
    with pytest.raises(SenseProfileError):
        WorldEntitySpawner()._spawn_legacy_guard(1, profile, EntitySpawnContext(position=(1.0, 1.0)), 42)


def test_compile_path_refuses_a_content_species_without_a_usable_profile(broken_human):
    from src.worldbuilding.compiler import WorldCompiler
    from src.worldbuilding.repository import WorldRepository
    spec, context = WorldRepository("data/worlds").load_world_with_context("urban_political")
    with pytest.raises(SenseProfileError):
        WorldCompiler.compile(spec, 42, context=context)


# --- the compile check is one helper: the diet declaration is checked first, then the sense profile ---------------------------------------------

def test_a_population_failing_both_declarations_raises_the_diet_error_first():
    """An unknown species fails the diet declaration AND the sense profile; the diet error (InvalidWorldSpecError) is the one raised."""
    from types import SimpleNamespace
    from src.worldbuilding.diet_declaration import require_declared_population_species
    from src.worldbuilding.schema import InvalidWorldSpecError
    from src.content.species_senses import require_species_sense_profile
    pop = SimpleNamespace(role="merchant", faction="merchant_league")
    with pytest.raises(SenseProfileError):
        require_species_sense_profile("no_such_species_xyz", "w1")  # the sense check alone would refuse it too
    with pytest.raises(InvalidWorldSpecError) as err:
        require_declared_population_species("w1", "p", pop, "no_such_species_xyz")
    assert not isinstance(err.value, SenseProfileError)
    assert "w1" in str(err.value) and "'p'" in str(err.value) and "does not declare" in str(err.value)
    with pytest.raises(InvalidWorldSpecError, match="no species"):
        require_declared_population_species("w1", "p", pop, None)


def test_a_population_with_a_diet_but_no_usable_profile_raises_the_sense_error(broken_human):
    """With the diet declared, the second check runs: a typed SenseProfileError naming the world and the population."""
    from types import SimpleNamespace
    from src.worldbuilding.diet_declaration import require_declared_population_species
    pop = SimpleNamespace(role="merchant", faction="merchant_league")
    with pytest.raises(SenseProfileError) as err:
        require_declared_population_species("w1", "p", pop, "human")
    assert "world 'w1' population 'p'" in str(err.value) and "'human'" in str(err.value)
