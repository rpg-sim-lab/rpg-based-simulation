"""
Tests for PerceptionGate.

Verifies:
- Wolf (predator_smell_senses) detects scent signal better than normal humanoid
- Spider (spider_vibration_senses) detects vibration signal
- Arcane (arcane_senses) detects magic_signal
- Normal humanoid cannot detect magic_signal
- Entity with no sense_profile_id uses baseline humanoid defaults
- Perception is deterministic for same inputs
- Gate never mutates catalog or entity
- PerceptionResult profile_source reflects profile used
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from src.content.repository import CatalogRepository
from src.world.perception.gate import PerceptionGate, PerceptionResult


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository("data/content")
    repo.load_all()
    return repo


@pytest.fixture(scope="module")
def gate(catalog):
    return PerceptionGate(catalog)


# PERC-02: senses come from the body's SPECIES (derived at read), so a test names a species, not a profile id.
_SPECIES_OF_PROFILE = {
    "predator_smell_senses": "wolf",
    "normal_humanoid_senses": "human",
    "spider_vibration_senses": "spider",
    "arcane_senses": "elf",
}


def _entity(sense_profile_id=None, species_id=None):
    species_id = species_id or _SPECIES_OF_PROFILE.get(sense_profile_id)
    props = {"species_id": species_id} if species_id else {}
    identity = SimpleNamespace(properties=props)
    return SimpleNamespace(identity=identity, kind=species_id or "fixture_kind_not_in_content")


# ---------------------------------------------------------------------------
# Archetype test cases
# ---------------------------------------------------------------------------

def test_wolf_detects_scent_signal(gate):
    """Predator smell profile has very_high smell; scent signal should be perceived."""
    wolf = _entity("predator_smell_senses")
    result = gate.can_perceive(wolf, {"scent": "medium"}, {"distance": 5.0})
    assert result.perceived, "Wolf should detect scent signal"
    assert "scent" in result.signals_used
    assert result.profile_source == "predator_smell_senses"


def test_normal_humanoid_weaker_scent_than_wolf(gate):
    """Normal humanoid has low smell; same scent signal → lower confidence than wolf."""
    human = _entity("normal_humanoid_senses")
    wolf = _entity("predator_smell_senses")
    ctx = {"distance": 5.0}
    human_result = gate.can_perceive(human, {"scent": "medium"}, ctx)
    wolf_result = gate.can_perceive(wolf, {"scent": "medium"}, ctx)
    assert wolf_result.confidence >= human_result.confidence


def test_spider_detects_vibration(gate):
    """Spider vibration profile has very_high vibration; vibration signal detected."""
    spider = _entity("spider_vibration_senses")
    result = gate.can_perceive(spider, {"vibration": "low"}, {"distance": 2.0})
    assert result.perceived, "Spider should detect vibration"
    assert "vibration" in result.signals_used
    assert result.profile_source == "spider_vibration_senses"


def test_arcane_entity_detects_magic_signal(gate):
    """Arcane senses profile has high magic_sense; magic_signal detected."""
    mage = _entity("arcane_senses")
    result = gate.can_perceive(mage, {"magic_signal": "high"}, {"distance": 3.0})
    assert result.perceived, "Arcane entity should detect magic signal"
    assert "magic_signal" in result.signals_used
    assert result.profile_source == "arcane_senses"


def test_normal_humanoid_cannot_detect_magic_signal(gate):
    """Normal humanoid has magic_sense=none; magic_signal not perceived."""
    human = _entity("normal_humanoid_senses")
    result = gate.can_perceive(human, {"magic_signal": "very_high"}, {"distance": 1.0})
    assert "magic_signal" not in result.signals_used


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------

def test_no_sense_profile_uses_baseline_humanoid(catalog):
    """A body whose species is not in content (no profile to derive) is unprofiled: baseline_humanoid defaults, and the read is counted per species."""
    gate = PerceptionGate(catalog)
    entity = _entity()
    result = gate.can_perceive(entity, {"visibility": "medium"})
    assert result.profile_source == "baseline_humanoid"
    assert result.perceived
    assert gate.unprofiled_counts == {"fixture_kind_not_in_content": 1}


def test_unknown_sense_profile_is_a_typed_error(catalog):
    """A species in content whose declared sense profile does not resolve is a content error (SenseProfileError), no longer a silent baseline (PERC-02)."""
    from src.world.perception.gate import SenseProfileError
    gate = PerceptionGate(catalog)
    human = catalog.species["human"]
    catalog.species["human"] = human.model_copy(update={"sense_profile": "nonexistent_profile_xyz"})
    try:
        with pytest.raises(SenseProfileError):
            gate.can_perceive(_entity(species_id="human"), {"visibility": "medium"})
    finally:
        catalog.species["human"] = human


# ---------------------------------------------------------------------------
# Determinism and immutability
# ---------------------------------------------------------------------------

def test_perception_is_deterministic(gate):
    wolf = _entity("predator_smell_senses")
    signals = {"scent": "medium", "noise": "low"}
    ctx = {"distance": 10.0, "alertness": 0.7}
    result_a = gate.can_perceive(wolf, signals, ctx)
    result_b = gate.can_perceive(wolf, signals, ctx)
    assert result_a == result_b


def test_gate_does_not_mutate_catalog(catalog):
    profile_count = len(catalog.sense_profiles) if hasattr(catalog, "sense_profiles") else None
    gate = PerceptionGate(catalog)
    entity = _entity("predator_smell_senses")
    gate.can_perceive(entity, {"scent": "high"})
    if profile_count is not None:
        assert len(catalog.sense_profiles) == profile_count


# ---------------------------------------------------------------------------
# Context effects
# ---------------------------------------------------------------------------

def test_high_distance_reduces_confidence(gate):
    wolf = _entity("predator_smell_senses")
    near = gate.can_perceive(wolf, {"scent": "high"}, {"distance": 1.0})
    far = gate.can_perceive(wolf, {"scent": "high"}, {"distance": 40.0})
    assert near.confidence > far.confidence


def test_no_signal_means_no_perception(gate):
    wolf = _entity("predator_smell_senses")
    result = gate.can_perceive(wolf, {"scent": "none"})
    assert "scent" not in result.signals_used
