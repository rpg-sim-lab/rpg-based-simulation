"""TCK-20261116-AN-ARM-RUNS-WHEN-THE-CACHE-PATH-IS-RELATIVE: a relative --cache (the paired-arms workflow passes ``--cache arm-cache``) must run an arm.

The child runs with the arm tree as its working directory; a relative tree string resolved a second time from inside it, so ``src`` was not importable (all nine
off-host arm jobs of run 43790499533 failed at once). The arm child is a stub script and the arm tree a stub package: no simulation, no git, no network."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.rpg_measure import paired
from tools.test_architecture import paired_arms as pa

SHA = "a" * 40
W, SEED, TICKS = "frontier_living_world", 42, 10
CHILD_SOURCE = (
    "import json, sys\n"
    "from src.marker import VALUE  # needs the ARM tree on sys.path (PYTHONPATH), as the real arm_child needs src.engine\n"
    "world, seed, ticks, out = sys.argv[1:5]\n"
    "from pathlib import Path\n"
    "Path(out).parent.mkdir(parents=True, exist_ok=True)\n"
    "Path(out).write_text(json.dumps({'world': world, 'seed': int(seed), 'marker': VALUE, 'runner': 'PINNED'}))\n"
)


def _stub_arm_tree(tree: Path) -> None:
    (tree / "src").mkdir(parents=True, exist_ok=True)
    (tree / "src" / "__init__.py").write_text("")
    (tree / "src" / "marker.py").write_text("VALUE = 'from-the-arm-tree'\n")


@pytest.fixture
def stub_child(tmp_path, monkeypatch):
    child = tmp_path / "stub_child.py"
    child.write_text(CHILD_SOURCE, encoding="utf-8")
    monkeypatch.setattr(paired, "CHILD", child)
    return child


def test_run_one_runs_an_arm_whose_tree_and_out_are_relative(tmp_path, monkeypatch, stub_child):
    monkeypatch.chdir(tmp_path)
    tree, out = Path("cache/trees/aaaaaaaaaaaa"), Path("cache/results/key/w_42.json")
    _stub_arm_tree(tree)
    paired.run_one(tree, W, SEED, TICKS, out)
    assert json.loads((tmp_path / out).read_text())["marker"] == "from-the-arm-tree"  # written where the parent looks, not under the tree
    assert not (tmp_path / tree / "cache").exists()
    assert (tmp_path / out.parent / paired.ENV_FILE).is_file()


def test_run_one_with_absolute_paths_is_unchanged(tmp_path, stub_child):
    tree, out = tmp_path / "cache" / "trees" / "aaaaaaaaaaaa", tmp_path / "cache" / "results" / "key" / "w_42.json"
    _stub_arm_tree(tree)
    paired.run_one(tree, W, SEED, TICKS, out)
    assert json.loads(out.read_text())["marker"] == "from-the-arm-tree"
    assert (out.parent / paired.ENV_FILE).is_file()


def _fake_prepare(cache: Path):
    def prepare_tree(repo, rev, cache_arg):
        tree = cache_arg / "trees" / SHA[:12]
        _stub_arm_tree(tree)
        return SHA, tree  # relative whenever the cache is, exactly as the real one returns it
    return prepare_tree


def _run_arm_cli(cache: str) -> int:
    return pa.main(["run-arm", "--repo", ".", "--sha", SHA, "--arm", "base", "--world", W, "--seed", str(SEED), "--ticks", str(TICKS), "--cache", cache])


def test_run_arm_with_a_relative_cache_writes_result_cost_and_env_under_the_resolved_cache(tmp_path, monkeypatch, stub_child):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(paired, "prepare_tree", _fake_prepare(Path("arm-cache")))
    assert _run_arm_cli("arm-cache") == 0
    resolved = (tmp_path / "arm-cache").resolve()
    result = paired.result_path(resolved, SHA, TICKS, W, SEED)
    assert json.loads(result.read_text())["marker"] == "from-the-arm-tree"
    assert (result.parent / paired.ENV_FILE).is_file()
    cost = json.loads(result.with_name(f"{W}_{SEED}.cost.json").read_text())
    assert cost["wall_seconds"] >= 0 and "runner" in cost


def test_run_arm_with_an_absolute_cache_lands_at_the_same_place_as_the_relative_one(tmp_path, monkeypatch, stub_child):
    absolute = tmp_path / "abs-cache"
    monkeypatch.setattr(paired, "prepare_tree", _fake_prepare(absolute))
    assert _run_arm_cli(str(absolute)) == 0
    result = paired.result_path(absolute, SHA, TICKS, W, SEED)
    assert result.is_file() and (result.parent / paired.ENV_FILE).is_file() and result.with_name(f"{W}_{SEED}.cost.json").is_file()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(paired, "prepare_tree", _fake_prepare(Path("rel-cache")))
    assert _run_arm_cli("rel-cache") == 0
    relative = paired.result_path((tmp_path / "rel-cache").resolve(), SHA, TICKS, W, SEED)
    assert relative.parent.name == result.parent.name  # the cache key does not depend on how the cache was spelt


def test_the_arm_child_and_so_every_cache_key_is_unchanged():
    assert paired.child_hash() == "9d13c131"  # the value at f94417e6f (keys 4eaab4d8b0a0-9d13c131-5000-aa066c26 ...)


def test_a_relative_out_lands_where_the_caller_means_not_inside_the_tree(tmp_path, monkeypatch, stub_child):
    """(d) the child's working directory is the tree, so a relative ``out`` is passed absolute; the tree here is absolute so only ``out`` is under test."""
    tree = tmp_path / "trees" / "aaaaaaaaaaaa"
    _stub_arm_tree(tree)
    monkeypatch.chdir(tmp_path)
    out = Path("results") / "key" / "w_42.json"
    paired.run_one(tree, W, SEED, TICKS, out)
    assert (tmp_path / out).is_file() and not (tree / out).exists()
