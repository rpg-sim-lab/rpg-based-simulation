"""F1/F2 (divergence 2.213; rpg-designer 2026-11-21): the way-round law's two numbers are a one-record catalog family (data/content/movement/wayround_settings.yaml), validated by their schema (both
integers >= 1, no cross-check) and part of the catalog fingerprint (the run's identity). The accessor reads the catalog, holds no state, and raises a typed error naming the file when the record is absent;
movement.py binds the values once, and they are the values the constants had (2 and 200: no behaviour change)."""
import shutil
from pathlib import Path

import pytest
import yaml

from src.content.repository import CatalogRepository
from src.content.schema import WayroundSettingsDefinition
from src.content.wayround_settings import WayroundSettings, WayroundSettingsError, wayround_settings

REAL = Path("data/content")
FILE = "movement/wayround_settings.yaml"


def _content_with(tmp_path, name="c", **values):
    """A copy of the shipped content whose way-round settings record carries ``values``."""
    root = tmp_path / name
    shutil.copytree(REAL, root, ignore=shutil.ignore_patterns("world_modules", "simulation_scenarios"))
    path = root / "movement" / "wayround_settings.yaml"
    records = yaml.safe_load(path.read_text())
    records[0].update(values)
    path.write_text(yaml.safe_dump(records))
    return root


def _load(root):
    repo = CatalogRepository(str(root))
    return repo, repo.load_all()


def test_the_shipped_catalog_says_two_and_two_hundred_and_loads_without_a_schema_error():
    repo, report = _load(REAL)
    assert FILE not in report.schema_errors
    assert wayround_settings(repo) == WayroundSettings(limit=2, quiet_ticks=200)


def test_movement_binds_the_values_the_constants_had_so_nothing_changes():
    """No behaviour change: the loaded values are 2 and 200 and the names movement exposes (and uses) equal them."""
    import src.engine.movement as movement

    assert (wayround_settings().limit, wayround_settings().quiet_ticks) == (2, 200)
    assert (movement.WAYROUND_LIMIT, movement.WAYROUND_QUIET_TICKS) == (2, 200)
    assert movement._wayround() is movement._wayround()  # bound once: the same object on every call


@pytest.mark.parametrize("key", ["wayround_limit", "wayround_quiet_ticks"])
@pytest.mark.parametrize("bad", ["2", 2.0, None, True, [2]])
def test_a_value_that_is_not_an_integer_is_refused_by_the_schema(key, bad):
    ok = {"wayround_limit": 2, "wayround_quiet_ticks": 200}
    with pytest.raises(ValueError):
        WayroundSettingsDefinition(id="wayround_settings", **{**ok, key: bad})


@pytest.mark.parametrize("key", ["wayround_limit", "wayround_quiet_ticks"])
@pytest.mark.parametrize("low", [0, -1])
def test_a_value_below_one_is_refused_by_the_schema(key, low):
    ok = {"wayround_limit": 2, "wayround_quiet_ticks": 200}
    with pytest.raises(ValueError):
        WayroundSettingsDefinition(id="wayround_settings", **{**ok, key: low})


def test_there_is_no_cross_check_between_the_two_values():
    """One counts steps, the other ticks: a limit larger than the window is valid."""
    assert WayroundSettingsDefinition(id="wayround_settings", wayround_limit=500, wayround_quiet_ticks=3).wayround_limit == 500


def test_a_missing_key_is_refused_by_the_schema():
    with pytest.raises(ValueError):
        WayroundSettingsDefinition(id="wayround_settings", wayround_limit=2)
    with pytest.raises(ValueError):
        WayroundSettingsDefinition(id="wayround_settings", wayround_quiet_ticks=200)


def test_a_bad_record_in_the_file_shows_up_as_that_files_schema_error_and_the_accessor_then_refuses(tmp_path):
    repo, report = _load(_content_with(tmp_path, wayround_quiet_ticks=0))
    assert FILE in report.schema_errors and "wayround_quiet_ticks" in report.schema_errors[FILE]
    with pytest.raises(WayroundSettingsError, match=r"movement/wayround_settings\.yaml.*wayround_limit"):
        wayround_settings(repo)


def test_a_catalog_without_the_record_is_a_typed_error_not_a_default(tmp_path):
    root = _content_with(tmp_path)
    (root / "movement" / "wayround_settings.yaml").unlink()
    repo, _ = _load(root)
    with pytest.raises(WayroundSettingsError, match="no record"):
        wayround_settings(repo)


def test_changing_a_value_changes_the_catalog_fingerprint(tmp_path):
    """The run's identity: the catalog fingerprint hashes every registered family's records, so a different value is a different run."""
    base, _ = _load(_content_with(tmp_path, "base"))
    again, _ = _load(_content_with(tmp_path, "again"))
    other_limit, _ = _load(_content_with(tmp_path, "limit", wayround_limit=3))
    other_quiet, _ = _load(_content_with(tmp_path, "quiet", wayround_quiet_ticks=201))
    assert base.fingerprint == again.fingerprint
    assert len({base.fingerprint, other_limit.fingerprint, other_quiet.fingerprint}) == 3
    assert wayround_settings(other_limit).limit == 3 and wayround_settings(other_quiet).quiet_ticks == 201
