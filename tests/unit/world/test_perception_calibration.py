"""PERC 3a (TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT; designer ruling, Option C).

An ordinary observer (baseline senses: vision medium, hearing medium, smell low) sees a STILL body by its size-dependent visibility only, by day to a distance that grows with the size, at night nearer
(vision two rungs lower). The calibration values are data (data/content/perception/perception_settings.yaml): threshold, fall-off and its floor, night steps, size visibility. Touch (d = 1) is separate.
"""
from __future__ import annotations

import ast
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from src.content.perception_settings import PerceptionSettingsError, perception_settings
from src.content.repository import CatalogRepository
from src.content.schema import PerceptionSettingsDefinition
from src.engine.perception_signals import emitted_signals
from src.world.perception.gate import DEFAULT_ALERTNESS, PerceptionGate, still_body_ceiling, validate_perception_settings

REAL = Path("data/content")
FILE = "perception/perception_settings.yaml"
GOOD = dict(perception_threshold=0.15, distance_falloff_per_tile=0.04, distance_factor_min=0.05, night_vision_steps=2,
            size_visibility={"small": "medium_high", "medium": "high", "large": "very_high"})


@pytest.fixture(scope="module")
def catalog():
    repo = CatalogRepository(str(REAL))
    repo.load_all()
    return repo


def _observer():
    """A body whose species is not in content: it perceives with the baseline senses (vision medium, hearing medium, smell low)."""
    return SimpleNamespace(kind="x", identity=SimpleNamespace(properties={"species_id": "not_in_content_kind"}), navigation=SimpleNamespace(lodged_in=None, last_moved_tick=None),
                           task=SimpleNamespace(work_kind="", payload={}), combat=SimpleNamespace(alive=True))


def _still_signals(catalog, size):
    """The signals of a still living body of ``size`` (derived by the one function, from the size map in data)."""
    return emitted_signals(_observer(), SimpleNamespace(size=size, signals={}), None, perception_settings(catalog).size_visibility)


def _reach(catalog, size, night):
    """The farthest whole distance at which the baseline observer perceives a still body of ``size`` (no touch: no `reach` in the context)."""
    gate = PerceptionGate(catalog)
    signals = _still_signals(catalog, size)
    seen = [d for d in range(0, 80) if gate.can_perceive(_observer(), signals, {"distance": float(d), "night": night}).perceived]
    return max(seen) if seen else -1


# --- the table (AC1-AC3), pinned for the shipped values --------------------------------------------------------------------------------

@pytest.mark.parametrize("size,night,farthest", [
    ("small", False, 13), ("medium", False, 15), ("large", False, 16),
    ("small", True, 2), ("medium", True, 6), ("large", True, 8),
])
def test_the_farthest_distance_a_still_body_is_seen_is_pinned(catalog, size, night, farthest):
    assert _reach(catalog, size, night) == farthest


def test_ac1_by_day_a_still_body_is_seen_at_its_size_distance_and_at_40_by_none(catalog):
    gate = PerceptionGate(catalog)
    for size, at_least in (("small", 4), ("medium", 8), ("large", 12)):
        assert gate.can_perceive(_observer(), _still_signals(catalog, size), {"distance": float(at_least)}).perceived, size
        assert not gate.can_perceive(_observer(), _still_signals(catalog, size), {"distance": 40.0}).perceived, size


def test_ac2_at_night_a_still_medium_and_a_still_small_body_are_seen_at_two_tiles(catalog):
    gate = PerceptionGate(catalog)
    for size in ("small", "medium"):
        assert gate.can_perceive(_observer(), _still_signals(catalog, size), {"distance": 2.0, "night": True}).perceived, size


def test_ac2_a_moving_body_is_still_heard_about_as_far_as_before(catalog):
    """Hearing medium x a moving body's noise (medium): perceived out to 11 tiles (the 02a value was 12); the new fall-off keeps noise reach about as it was."""
    gate = PerceptionGate(catalog)
    moving = {"noise": "medium"}
    seen = [d for d in range(0, 60) if gate.can_perceive(_observer(), moving, {"distance": float(d)}).perceived]
    assert max(seen) == 11


def test_ac3_a_larger_body_scores_at_least_as_high_at_every_distance_day_and_night(catalog):
    gate = PerceptionGate(catalog)
    for night in (False, True):
        for d in range(1, 40):
            scores = [gate.can_perceive(_observer(), _still_signals(catalog, s), {"distance": float(d), "night": night}).confidence for s in ("small", "medium", "large")]
            assert scores[0] <= scores[1] <= scores[2], (d, night, scores)
    sizes = perception_settings(catalog).size_visibility
    assert len({sizes["small"], sizes["medium"], sizes["large"]}) == 3


def test_a_still_body_is_never_heard_or_smelled_only_seen(catalog):
    """The threshold sits above the still-body ceiling, so the hearing and smell channels never carry a still body at the default alertness."""
    gate = PerceptionGate(catalog)
    res = gate.can_perceive(_observer(), {"noise": "low", "scent": "medium", "vibration": "low"}, {"distance": 0.0})
    assert not res.perceived
    assert still_body_ceiling() == pytest.approx(0.135) and perception_settings(catalog).perception_threshold > still_body_ceiling()


def test_the_margin_holds_only_at_the_default_alertness(catalog):
    """R3 (known limit): at alertness 1.0 a baseline observer's still-hearing score is 0.18, above the 0.15 threshold: whoever wires alertness re-checks the margin."""
    gate = PerceptionGate(catalog)
    assert gate.can_perceive(_observer(), {"noise": "low"}, {"distance": 0.0, "alertness": 1.0}).perceived
    assert not gate.can_perceive(_observer(), {"noise": "low"}, {"distance": 0.0, "alertness": DEFAULT_ALERTNESS}).perceived


def test_no_src_caller_passes_alertness_to_the_gate():
    """R3 guard: alertness is never passed by a src caller (gate.py is the only reader). A dict with the gate's context keys that also carries `alertness`, or an `alertness=` keyword to
    `can_perceive`, fails here: the 10% threshold margin holds only at the default."""
    offenders = []
    for path in sorted(Path("src").rglob("*.py")):
        if path.as_posix() == "src/world/perception/gate.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = {k.value for k in node.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                if "alertness" in keys and keys & {"distance", "reach", "night", "terrain_modifier"}:
                    offenders.append(f"{path}:{node.lineno} context dict with alertness")
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "can_perceive" and any(kw.arg == "alertness" for kw in node.keywords):
                offenders.append(f"{path}:{node.lineno} can_perceive(alertness=)")
    assert not offenders, offenders


# --- load checks (AC4) --------------------------------------------------------------------------------------------------------------------

def _catalog_with(**values):
    return SimpleNamespace(perception_settings={"perception_settings": PerceptionSettingsDefinition(id="perception_settings", **{**GOOD, **values})})


def test_the_shipped_catalog_loads_with_the_ruled_values(catalog):
    s = perception_settings(catalog)
    assert (s.perception_threshold, s.distance_falloff_per_tile, s.distance_factor_min, s.night_vision_steps) == (0.15, 0.04, 0.05, 2)
    assert dict(s.size_visibility) == GOOD["size_visibility"]
    validate_perception_settings(s)
    PerceptionGate(catalog)  # builds and validates


def test_a_threshold_at_or_below_the_still_body_ceiling_is_refused_naming_the_values():
    with pytest.raises(PerceptionSettingsError, match="strictly above the still-body ceiling"):
        PerceptionGate(_catalog_with(perception_threshold=still_body_ceiling()))
    with pytest.raises(PerceptionSettingsError, match="strictly above"):
        PerceptionGate(_catalog_with(perception_threshold=0.1))
    PerceptionGate(_catalog_with(perception_threshold=still_body_ceiling() + 0.001))


def test_a_distance_factor_floor_that_alone_admits_a_channel_is_refused():
    with pytest.raises(PerceptionSettingsError, match="floor alone would admit"):
        PerceptionGate(_catalog_with(distance_factor_min=0.15))


@pytest.mark.parametrize("bad", [
    dict(perception_threshold=0.0), dict(perception_threshold=1.5), dict(distance_falloff_per_tile=0.0), dict(distance_falloff_per_tile=0.5), dict(distance_factor_min=1.0),
    dict(night_vision_steps=-1), dict(night_vision_steps=2.0),
    dict(size_visibility={"small": "high", "medium": "high", "large": "very_high"}),
    dict(size_visibility={"small": "high", "medium": "medium_high", "large": "very_high"}),
    dict(size_visibility={"small": "medium_high", "medium": "high"}),
    dict(size_visibility={"small": "bogus", "medium": "high", "large": "very_high"}),
])
def test_a_bad_value_is_refused_by_the_schema(bad):
    with pytest.raises(ValueError):
        PerceptionSettingsDefinition(id="perception_settings", **{**GOOD, **bad})


def test_a_catalog_without_the_record_is_a_typed_error_naming_the_file():
    with pytest.raises(PerceptionSettingsError, match="perception_settings.yaml"):
        PerceptionGate(SimpleNamespace(perception_settings={}))


def test_an_undeclared_size_gives_off_the_medium_entry(catalog):
    s = perception_settings(catalog)
    assert s.undeclared_visibility == s.size_visibility["medium"]
    assert emitted_signals(_observer(), None, None, s.size_visibility)["visibility"] == s.size_visibility["medium"]


def test_changing_a_value_changes_the_catalog_fingerprint(tmp_path):
    def load(name, **values):
        root = tmp_path / name
        shutil.copytree(REAL, root, ignore=shutil.ignore_patterns("world_modules", "simulation_scenarios"))
        path = root / FILE
        records = yaml.safe_load(path.read_text())
        records[0].update(values)
        path.write_text(yaml.safe_dump(records))
        repo = CatalogRepository(str(root))
        repo.load_all()
        return repo

    a, a_again, b = load("a"), load("a_again"), load("b", perception_threshold=0.16)
    assert a.fingerprint == a_again.fingerprint
    assert a.fingerprint != b.fingerprint
    assert perception_settings(b).perception_threshold == 0.16
