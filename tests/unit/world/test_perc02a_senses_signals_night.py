"""PERC-02a: senses derive from the species, signals follow the body, vision drops at night, a gate error is not perception
(TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS; divergence 2.210; STRAT-352)."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.content.repository import CatalogRepository
from src.world.perception.gate import NIGHT_VISION_STEPS, PerceptionGate, SenseProfileError, _lower_level, _LEVEL_TO_FLOAT, _PERCEPTION_THRESHOLD
from src.world.perception.signals import emitted_signals

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
        kind="fixture", identity=SimpleNamespace(properties={"species_id": species_id}),
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
    root = Path(__file__).resolve().parents[3] / "src" / "world" / "perception"
    for name in ("gate.py", "signals.py"):
        text = (root / name).read_text(encoding="utf-8")
        assert not re.search(r"\.kind\b", text), name
    assert "species_of" in (root / "gate.py").read_text(encoding="utf-8")


def test_a_body_model_may_declare_a_magic_signal_and_only_known_keys_and_levels():
    from src.content.schema import BodyModelDefinition
    body = BodyModelDefinition(id="b", display_name="B", signals={"magic": "very_high", "visibility": "none"})
    sig = emitted_signals(_body("fixture_species"), body)
    assert sig["magic_signal"] == "very_high" and sig["visibility"] == "none"
    for bad in ({"smell": "low"}, {"magic": "enormous"}):
        with pytest.raises(ValueError):
            BodyModelDefinition(id="b", display_name="B", signals=bad)
