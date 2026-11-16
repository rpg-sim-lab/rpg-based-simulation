"""The host's Test-phase cap loader (TCK-20261115-TEST-PHASE-RUNS-TESTS-TOOLS-UNCAPPED-IN-ONE-PROCESS)."""

from pathlib import Path

import pytest
import yaml

from tools.delivery.host_test_caps import CAPS_REL, PROJECT_REL, HostCap, host_tag, load_cap

_ENTRY = {"memory_max": "3G", "memory_swap_max": 0, "cpus": "4-5", "mem_available_floor_gb": 3, "max_tests_per_chunk": 700}


def _write(root: Path, rel: Path, data: dict) -> None:
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_text(yaml.safe_dump(data), encoding="utf-8")


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    _write(tmp_path, CAPS_REL, {"hosts": {"alpha": dict(_ENTRY), "beta": {**_ENTRY, "memory_max": "2.5G"}}})
    _write(tmp_path, PROJECT_REL, {"host_names": {"alpha-Virtual-Machine": "alpha", "beta-box": "beta"}})
    return tmp_path


def test_a_listed_hostname_resolves_to_its_tag_and_that_tags_cap(root):
    assert host_tag(root, "alpha-Virtual-Machine") == "alpha"
    cap = load_cap(root, host_tag(root, "beta-box"), env={})
    assert cap == HostCap("beta", "2.5G", "0", "4-5", 3.0, 700)


def test_an_unlisted_hostname_falls_through_to_the_raw_name_then_to_no_entry(root):
    assert host_tag(root, "gamma") == "gamma"
    assert load_cap(root, host_tag(root, "gamma"), env={}) is None


def test_a_raw_hostname_that_is_itself_a_tag_still_finds_its_entry(root):
    assert host_tag(root, "alpha") == "alpha"
    assert load_cap(root, host_tag(root, "alpha"), env={}).memory_max == "3G"


def test_env_overrides_replace_single_numbers_for_one_run(root):
    cap = load_cap(root, "alpha", env={"RPG_TEST_CAP_MEMORY_MAX": "1G", "RPG_TEST_CAP_MAX_TESTS_PER_CHUNK": "50"})
    assert (cap.memory_max, cap.max_tests_per_chunk, cap.cpus) == ("1G", 50, "4-5")


def test_an_incomplete_or_malformed_entry_means_no_cap(root):
    _write(root, CAPS_REL, {"hosts": {"alpha": {"memory_max": "3G"}, "beta": {**_ENTRY, "max_tests_per_chunk": "many"}}})
    assert load_cap(root, "alpha", env={}) is None
    assert load_cap(root, "beta", env={}) is None


def test_a_missing_or_unreadable_registry_means_no_cap(tmp_path):
    assert load_cap(tmp_path, "alpha", env={}) is None
    (tmp_path / CAPS_REL).parent.mkdir(parents=True)
    (tmp_path / CAPS_REL).write_text("hosts: [unclosed", encoding="utf-8")
    assert load_cap(tmp_path, "alpha", env={}) is None


def test_the_committed_registry_holds_only_host_tags_and_cap_numbers():
    repo = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((repo / CAPS_REL).read_text(encoding="utf-8"))
    assert set(data) == {"hosts"}
    for tag, entry in data["hosts"].items():
        assert set(entry) == {"memory_max", "memory_swap_max", "cpus", "mem_available_floor_gb", "max_tests_per_chunk"}, tag
        assert load_cap(repo, tag, env={}) is not None, tag
