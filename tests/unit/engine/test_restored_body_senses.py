"""TCK-20261118-CAMPAIGN-RUNNER-AND-RESTORED-BODIES-SKIP-THE-BUILD-TIME-SENSES-CHECK, restore half (PERC-02a, STRAT-352).

A checkpoint saved under content A and restored under content B is refused before any tick when one body's species has lost its sense profile.
rpg-designer ruling: the typed error is RestoredBodySenseProfileError(ValueError) with the SenseProfileError as ``__cause__``."""
from __future__ import annotations

import pytest

from src.content.repository import CatalogRepository
from src.core.builder import V2EntityBuilder
from src.core.species import SenseProfileError
from src.engine.checkpoint import CanonicalStateHasher
from src.engine.checkpoint_senses import RestoredBodySenseProfileError, check_restored_body_senses
from tests.named_run_dirs import remove_restored_run_dirs  # noqa: F401

pytestmark = pytest.mark.usefixtures("remove_restored_run_dirs")


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture()
def content_b(catalog):
    """Content B: the module catalog installed as the warmed one, with ``human`` declaring a sense profile that does not exist."""
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    human = catalog.species["human"]
    catalog.species["human"] = human.model_copy(update={"sense_profile": "nope"})
    configure_behavior_consumers(catalog)
    try:
        yield catalog
    finally:
        catalog.species["human"] = human
        reset_behavior_consumers()


def _state(*kinds):
    return type("S", (), {"entities": {i + 1: V2EntityBuilder(i + 1).kind(k).location(float(i), 0.0).build() for i, k in enumerate(kinds)}})()


def test_a_state_whose_species_are_all_profiled_passes(catalog):
    check_restored_body_senses(_state("human", "wolf"), "ckpt.bin", catalog)


def test_an_unprofiled_species_is_refused_naming_the_checkpoint_entity_and_species(content_b):
    with pytest.raises(RestoredBodySenseProfileError) as err:
        check_restored_body_senses(_state("wolf", "human"), "saved/ckpt.bin")
    assert isinstance(err.value, ValueError)
    assert isinstance(err.value.__cause__, SenseProfileError)
    assert "saved/ckpt.bin" in str(err.value) and "entity 2" in str(err.value) and "'human'" in str(err.value)


def test_a_species_missing_from_content_is_refused_too(catalog):
    with pytest.raises(RestoredBodySenseProfileError):
        check_restored_body_senses(_state("human", "no_such_species_xyz"), "ckpt.bin", catalog)


@pytest.mark.slow
def test_restore_under_content_b_is_refused_before_any_tick_and_under_unchanged_content_succeeds(tmp_path, catalog):
    from src.core.state import AuthoritativeState
    from src.engine.behavior_consumers import configure_behavior_consumers, reset_behavior_consumers
    from src.engine.scenario_checkpoint import ScenarioCheckpointer
    from src.engine.scenario_runtime import ScenarioRuntimeService
    from src.scenarios.schema import SimulationScenarioDefinition
    from src.systems.world_systems.generator import EntityGenerator

    spec = SimulationScenarioDefinition(id="restore_senses", world_composition="frontier_living_world", perspective="hero_guild_perspective")
    gen = EntityGenerator(7)
    hero, goblin = gen.spawn_hero((10.0, 10.0)), gen.spawn_goblin((12.0, 12.0))
    svc = ScenarioRuntimeService(spec, initial_state=AuthoritativeState(tick=0, seed=7, entities={hero.id: hero, goblin.id: goblin}))
    path = tmp_path / "ckpt.bin"
    try:
        svc.start(tick_limit=3)
        saved_hash = CanonicalStateHasher.get_hash(svc._kernel.state)
        ScenarioCheckpointer.save(svc, path)
    finally:
        svc.abort()

    configure_behavior_consumers(catalog)  # content A: unchanged
    try:
        restored = ScenarioCheckpointer.restore(path, spec)
        try:
            assert restored.tick == 3
            assert CanonicalStateHasher.get_hash(restored._kernel.state) == saved_hash
        finally:
            restored.abort()
    finally:
        reset_behavior_consumers()

    original = catalog.species["goblin"]
    catalog.species["goblin"] = original.model_copy(update={"sense_profile": "nope"})  # content B: one saved body's species lost its profile
    configure_behavior_consumers(catalog)
    try:
        with pytest.raises(RestoredBodySenseProfileError) as err:
            ScenarioCheckpointer.restore(path, spec)
        assert isinstance(err.value.__cause__, SenseProfileError)
        assert "'goblin'" in str(err.value)
    finally:
        catalog.species["goblin"] = original
        reset_behavior_consumers()
