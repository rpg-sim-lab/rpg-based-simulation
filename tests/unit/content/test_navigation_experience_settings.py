"""The #996 rework (design section 9): the navigation experience settings are a one-record catalog family, so the four values are validated by their schema (integers >= 1) and are part of the catalog
fingerprint (the run's identity). The accessor reads the catalog, holds no state, and raises a typed error naming the file when the record is absent."""
import shutil
from pathlib import Path

import pytest
import yaml

from src.content.navigation_experience_settings import NavigationExperienceSettings, NavigationExperienceSettingsError, navigation_experience_settings
from src.content.repository import CatalogRepository
from src.content.schema import NavigationExperienceSettingsDefinition

REAL = Path("data/content")
FILE = "strategy/navigation_experience_settings.yaml"
KEYS = ("oscillation_review_delay", "bodies_review_delay", "approach_change_radius", "navigation_experience_cap")


def _content_with(tmp_path, name="c", **values):
    """A copy of the shipped content whose settings record carries ``values``."""
    root = tmp_path / name
    shutil.copytree(REAL, root, ignore=shutil.ignore_patterns("world_modules", "simulation_scenarios"))
    path = root / "strategy" / "navigation_experience_settings.yaml"
    records = yaml.safe_load(path.read_text())
    records[0].update(values)
    path.write_text(yaml.safe_dump(records))
    return root


def _load(root):
    repo = CatalogRepository(str(root))
    return repo, repo.load_all()


def test_the_shipped_catalog_says_100_50_5_8_and_loads_without_a_schema_error():
    repo, report = _load(REAL)
    assert FILE not in report.schema_errors
    assert navigation_experience_settings(repo) == NavigationExperienceSettings(100, 50, 5, 8)


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("bad", ["4", 4.0, None, True, [4], 0, -1])
def test_a_value_that_is_not_an_integer_of_at_least_one_is_refused_by_the_schema(key, bad):
    values = {k: 4 for k in KEYS}
    values[key] = bad
    with pytest.raises(ValueError):
        NavigationExperienceSettingsDefinition(id="navigation_experience_settings", **values)


def test_a_missing_key_is_refused_by_the_schema():
    with pytest.raises(ValueError):
        NavigationExperienceSettingsDefinition(id="navigation_experience_settings", oscillation_review_delay=100)


def test_a_bad_record_in_the_file_shows_up_as_that_files_schema_error_and_the_accessor_then_refuses(tmp_path):
    repo, report = _load(_content_with(tmp_path, bodies_review_delay=0))
    assert FILE in report.schema_errors and "bodies_review_delay" in report.schema_errors[FILE]
    with pytest.raises(NavigationExperienceSettingsError, match=r"navigation_experience_settings\.yaml"):
        navigation_experience_settings(repo)


def test_a_catalog_without_the_record_is_a_typed_error_not_a_default(tmp_path):
    root = _content_with(tmp_path)
    (root / "strategy" / "navigation_experience_settings.yaml").unlink()
    repo, _ = _load(root)
    with pytest.raises(NavigationExperienceSettingsError, match="no record"):
        navigation_experience_settings(repo)


def test_changing_a_value_changes_the_catalog_fingerprint(tmp_path):
    """The run's identity: the catalog fingerprint hashes every registered family's records, so a different value is a different run."""
    a, _ = _load(_content_with(tmp_path, "a"))
    a_again, _ = _load(_content_with(tmp_path, "a_again"))
    b, _ = _load(_content_with(tmp_path, "b", approach_change_radius=6))
    assert a.fingerprint == a_again.fingerprint
    assert a.fingerprint != b.fingerprint
    assert navigation_experience_settings(b).approach_change_radius == 6
