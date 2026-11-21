"""F2 (divergence 2.220): the blocker settings are a one-record catalog family, so the value is validated by its schema (an integer >= 1) and is part of the catalog fingerprint (the run's identity).
The accessor reads the catalog, holds no state, and raises a typed error naming the file and the key when the record is absent."""
import shutil
from pathlib import Path

import pytest
import yaml

from src.content.blocker_settings import BlockerSettingsError, access_giveup_limit
from src.content.repository import CatalogRepository
from src.content.schema import BlockerSettingsDefinition

REAL = Path("data/content")


def _content_with_limit(tmp_path, limit, name="c"):
    """A copy of the shipped content whose blocker settings record carries ``limit``."""
    root = tmp_path / name
    shutil.copytree(REAL, root, ignore=shutil.ignore_patterns("world_modules", "simulation_scenarios"))
    path = root / "strategy" / "blocker_settings.yaml"
    records = yaml.safe_load(path.read_text())
    records[0]["access_giveup_limit"] = limit
    path.write_text(yaml.safe_dump(records))
    return root


def _load(root):
    repo = CatalogRepository(str(root))
    return repo, repo.load_all()


def test_the_shipped_catalog_says_four_and_loads_without_a_schema_error():
    repo, report = _load(REAL)
    assert "strategy/blocker_settings.yaml" not in report.schema_errors
    assert access_giveup_limit(repo) == 4


@pytest.mark.parametrize("bad", ["4", 4.0, None, True, [4]])
def test_a_value_that_is_not_an_integer_is_refused_by_the_schema(bad):
    with pytest.raises(ValueError):
        BlockerSettingsDefinition(id="blocker_settings", access_giveup_limit=bad)


@pytest.mark.parametrize("low", [0, -1])
def test_a_limit_below_one_is_refused_by_the_schema(low):
    with pytest.raises(ValueError):
        BlockerSettingsDefinition(id="blocker_settings", access_giveup_limit=low)


def test_a_missing_key_is_refused_by_the_schema():
    with pytest.raises(ValueError):
        BlockerSettingsDefinition(id="blocker_settings")


def test_a_bad_record_in_the_file_shows_up_as_that_files_schema_error_and_the_accessor_then_refuses(tmp_path):
    repo, report = _load(_content_with_limit(tmp_path, 0))
    assert "strategy/blocker_settings.yaml" in report.schema_errors and "access_giveup_limit" in report.schema_errors["strategy/blocker_settings.yaml"]
    with pytest.raises(BlockerSettingsError, match=r"strategy/blocker_settings\.yaml.*access_giveup_limit"):
        access_giveup_limit(repo)


def test_a_catalog_without_the_record_is_a_typed_error_not_a_default(tmp_path):
    root = _content_with_limit(tmp_path, 4)
    (root / "strategy" / "blocker_settings.yaml").unlink()
    repo, _ = _load(root)
    with pytest.raises(BlockerSettingsError, match="no record"):
        access_giveup_limit(repo)


def test_changing_the_limit_changes_the_catalog_fingerprint(tmp_path):
    """The run's identity: the catalog fingerprint hashes every registered family's records, so a different limit is a different run."""
    four, _ = _load(_content_with_limit(tmp_path, 4, "four"))
    four_again, _ = _load(_content_with_limit(tmp_path, 4, "four_again"))
    five, _ = _load(_content_with_limit(tmp_path, 5, "five"))
    assert four.fingerprint == four_again.fingerprint
    assert four.fingerprint != five.fingerprint
    assert access_giveup_limit(five) == 5
